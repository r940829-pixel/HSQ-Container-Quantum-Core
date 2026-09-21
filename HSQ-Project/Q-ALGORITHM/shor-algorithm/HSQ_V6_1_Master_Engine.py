# ==============================================================================
# HSQ V6.5 TOPOLOGICAL SHOR MASTER ENGINE (ANALYTIC & ALIGNMENT RESET EDITION)
# Fixed: Zero Shot-Noise Analytics + Target Phase Alignment Reset + O(N) Interlock.
# ==============================================================================

import os
import sys
import time
import math
import secrets
import logging
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction

import numpy as np
import redis
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(100000)

logging.getLogger("urllib3").setLevel(logging.ERROR)

SERVER_IP  = os.environ.get("HSQ_SERVER_IP", "127.0.0.1")
BASE_PORT  = int(os.environ.get("HSQ_BASE_PORT", 5011))
REDIS_PORT = int(os.environ.get("TENSOR_BUS_PORT", 2057))

DISCOVERY_TIMEOUT = 5.0
EXECUTION_TIMEOUT = 5.0
MAX_RETRY_COUNT   = 3
MAX_CONCURRENT_WORKERS = 64

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class UniversalHSQShorMasterEngine:
    def __init__(self, target_M: int, target_org: str = "Quantum Evaluation Board", max_trials: int = 10):
        self.M = int(target_M)
        self.target_org = target_org
        self.max_trials = max_trials
        
        # 根據大數 M 位元長度，動態計算 Control 與 Target 節點數
        self.L_target = self.M.bit_length()
        self.t_control = 2 * self.L_target
        self.total_nodes_needed = self.t_control + 1  # 拓樸映射僅需 1 顆 Target 節點
        
        self.tested_coprimes: Set[int] = set()
        self.start_wall_time = time.time()

        logging.info("====================================================================")
        logging.info("   HSQ V6.5 SHOR MASTER ENGINE (ANALYTIC INTERFEROMETRY EDITION)   ")
        logging.info("====================================================================")
        logging.info(f"👉 Target Integer (M) : {self.M}")
        logging.info(f"👉 Reg1 (Control)     : {self.t_control} Nodes (Resolution: 1/{2**self.t_control})")
        logging.info(f"👉 Reg2 (Target)      : 1 Node (HSQ Phase Topological Mapper)")
        logging.info(f"👉 Observation Mode   : Pure Native Geometric Metric Projection (Zero Shots)")
        
        # 連接 Redis Switch 匯流排
        try:
            self.redis_bus = redis.Redis(host=SERVER_IP, port=REDIS_PORT, db=0, decode_responses=True, socket_timeout=2.0)
            self.redis_bus.ping()
        except Exception as e:
            logging.error(f"❌ Redis Switch Connection Error: {e}")
            sys.exit(1)

        # 高併發 HTTP 連線池建立
        self.http_session = requests.Session()
        retry_strategy = Retry(total=MAX_RETRY_COUNT, backoff_factor=0.02, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=MAX_CONCURRENT_WORKERS, pool_maxsize=MAX_CONCURRENT_WORKERS, max_retries=retry_strategy)
        self.http_session.mount('http://', adapter)

        # 自動探測 HSQ 節點 Ports
        self.active_ports = self._discover_hsq_nodes()
        if len(self.active_ports) < self.total_nodes_needed:
            logging.error(f"❌ Active Nodes ({len(self.active_ports)}) < Required ({self.total_nodes_needed})")
            sys.exit(1)

        self.reg1_ports = self.active_ports[:self.t_control]
        self.target_port = self.active_ports[self.t_control]
        logging.info(f"✅ HSQ Nodes Ready. Control Ports: {self.reg1_ports[0]}~{self.reg1_ports[-1]} | Target Port: {self.target_port}")

    def _discover_hsq_nodes(self) -> List[int]:
        def probe(port):
            try:
                res = self.http_session.get(f"http://{SERVER_IP}:{port}/ping", timeout=DISCOVERY_TIMEOUT)
                if res.status_code == 200 and res.json().get("status") == "ready":
                    return port
            except: pass
            return None
        max_ports = max(100, self.total_nodes_needed * 2)
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            return [p for p in executor.map(probe, list(range(BASE_PORT, BASE_PORT + max_ports))) if p is not None]

    def _post_single(self, port: int, endpoint: str, payload: dict = None) -> Optional[dict]:
        try:
            return self.http_session.post(f"http://{SERVER_IP}:{port}/{endpoint}", json=payload or {}, timeout=EXECUTION_TIMEOUT).json()
        except: return None

    def _post_parallel(self, ports: List[int], endpoint: str, payload_builder_func) -> List[Optional[dict]]:
        results = [None] * len(ports)
        with ThreadPoolExecutor(max_workers=min(len(ports), MAX_CONCURRENT_WORKERS)) as executor:
            future_to_idx = {executor.submit(self._post_single, port, endpoint, payload_builder_func(i, port)): i for i, port in enumerate(ports)}
            for future in as_completed(future_to_idx):
                results[future_to_idx[future]] = future.result()
        return results

    def _get_unique_coprime(self) -> int:
        while True:
            a_gen = secrets.randbelow(self.M - 2) + 2
            if math.gcd(a_gen, self.M) == 1 and a_gen not in self.tested_coprimes:
                self.tested_coprimes.add(a_gen)
                return a_gen

    def _validate_and_refine_period(self, a: int, raw_r: int) -> Optional[int]:
        if raw_r <= 0: return None
        if pow(a, raw_r, self.M) != 1:
            found_r = None
            for m in [1, 2, 3, 4]:
                for offset in [0, -1, 1, -2, 2]:
                    candidate = raw_r * m + offset
                    if candidate > 0 and pow(a, candidate, self.M) == 1:
                        found_r = candidate; break
                if found_r: break
            if not found_r: return None
            raw_r = found_r
        r_min = raw_r
        for d in range(1, int(math.isqrt(raw_r)) + 1):
            if raw_r % d == 0:
                if pow(a, d, self.M) == 1: r_min = min(r_min, d)
                if pow(a, raw_r // d, self.M) == 1: r_min = min(r_min, raw_r // d)
        return r_min

    def _run_single_quantum_trial(self, trial_num: int, a_generator: int) -> Tuple[str, Any, Any, Any, Any, Any]:
        trial_start = time.time()
        logging.info(f"\n====================================================================")
        logging.info(f"   🚀 TRIAL #{trial_num} / {self.max_trials} | Generator a = {a_generator}")
        logging.info(f"====================================================================")

        all_used_ports = self.reg1_ports + [self.target_port]
        self._post_parallel(all_used_ports, "reset", lambda i, p: {})
        
        # 1. 準備 Control (H門) 與 Target (|1>態)
        self._post_parallel(self.reg1_ports, "instruction", lambda i, p: {"gate": "h"})
        self._post_single(self.target_port, "instruction", {"gate": "x"})

        # ====================================================================
        # Phase 1: 🌟 拓樸場 Phase Kickback (帶 Alignment Reset 重置機制)
        # ====================================================================
        logging.info("⚛️ Injecting Phase Kickback with Target Phase Alignment Reset...")
        
        for j, reg1_port in enumerate(self.reg1_ports):
            target_bus = f"shor_t{trial_num}_q{j}"
            # 廣播 Target |1> 態特徵 Metric
            self._post_single(self.target_port, "instruction", {"gate": "export_tensor_metric", "bus_key": target_bus})

            # 計算模冪項映射角度: a^(2^j) mod M
            mod_val = pow(a_generator, 2**j, self.M)
            phase_angle = float(2.0 * np.pi * (mod_val / self.M))

            # 雙向 Kickback: 對 Control Node 施加相角
            self._post_single(reg1_port, "instruction", {
                "gate": "cphase", 
                "delta_phi": phase_angle, 
                "source_bus_key": target_bus
            })

            # 🌟 重點修正：清除 Target 波包殘留相角，防止下一階位元退相干
            self._post_single(self.target_port, "reset")
            self._post_single(self.target_port, "instruction", {"gate": "x"})

        # ====================================================================
        # Phase 2: 真·逆量子傅立葉變換 (IQFT) 拓樸干涉
        # ====================================================================
        logging.info("⚛️ Executing Dynamic IQFT Topology...")
        for i in range(self.t_control - 1, -1, -1):
            port_i = self.reg1_ports[i]
            for j in range(self.t_control - 1, i, -1):
                port_j = self.reg1_ports[j]
                bus_key_j = f"dyn_iqft_q{j}_t{trial_num}"
                
                self._post_single(port_j, "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                iqft_angle = -np.pi / (2 ** (j - i))
                
                self._post_single(port_i, "instruction", {"gate": "cphase", "delta_phi": iqft_angle, "source_bus_key": bus_key_j})
            
            # H 門旋轉導出軸向干涉
            self._post_single(port_i, "instruction", {"gate": "h"})

        # ====================================================================
        # Phase 3: 幾何干涉 Spinor 投影解析 (Zero Shot-Noise Analytics)
        # ====================================================================
        logging.info("📊 Reading Native Geometric Spinor Metrics...")
        analytic_bits = []
        probabilities = []

        for i, port in enumerate(self.reg1_ports):
            res = self._post_single(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"final_meas_q{i}"})
            if res and "state_b" in res:
                prob_1 = np.clip(res["state_b"][0]**2 + res["state_b"][1]**2, 0.0, 1.0)
                probabilities.append(prob_1)
                analytic_bits.append("1" if prob_1 > 0.5 else "0")
            else:
                probabilities.append(0.0)
                analytic_bits.append("0")

        # 解算十進位相位 theta
        theta_est = 0.0
        for idx, bit in enumerate(analytic_bits):
            if bit == "1":
                theta_est += 1.0 / (2 ** (idx + 1))

        bitstring = "".join(analytic_bits)
        logging.info(f"  ├─ Geometric Bitstring : 0.{bitstring}")
        logging.info(f"  └─ Derived Phase (θ)   : {theta_est:.10f}")

        # ====================================================================
        # Phase 4: 古典連分數與質因數求解
        # ====================================================================
        if theta_est == 0.0:
            logging.warning("⚠️ Phase is 0.0, retrying with another generator...")
            return "FAILURE_ZERO_PHASE", a_generator, None, None, None, None

        frac = Fraction(theta_est).limit_denominator(self.M)
        raw_r = frac.denominator
        r_period = self._validate_and_refine_period(a_generator, raw_r)

        if r_period and r_period % 2 == 0:
            half_power = pow(a_generator, r_period // 2, self.M)
            if half_power != self.M - 1 and half_power != 1:
                factor_1 = math.gcd(half_power - 1, self.M)
                factor_2 = self.M // factor_1
                if 1 < factor_1 < self.M:
                    trial_duration = time.time() - trial_start
                    logging.info("====================================================================")
                    logging.info(f"🏆 [SUCCESS] Factored {self.M} = {factor_1} * {factor_2}")
                    logging.info(f"⏱️ Trial Duration : {trial_duration * 1000:.2f} ms")
                    logging.info("====================================================================")
                    return "SUCCESS", a_generator, r_period, theta_est, factor_1, factor_2

        logging.warning("⚠️ Could not yield a valid non-trivial factor. Retrying...")
        return "FAILURE_NO_VALID_PEAK", a_generator, None, None, None, None

    def execute_shor_factorization(self):
        for trial in range(1, self.max_trials + 1):
            a_gen = self._get_unique_coprime()
            status, a, r, theta, f1, f2 = self._run_single_quantum_trial(trial, a_gen)
            if status == "SUCCESS":
                break

if __name__ == "__main__":
    print("====================================================================")
    print("===   HSQ V6.5 SHOR FACTORIZATION MASTER (ANALYTIC EDITION)       ===")
    print("====================================================================")
    try:
        user_in = input("👉 Enter target integer to factorize (e.g., 15, 21, 35): ").strip()
        target = int(user_in)
    except Exception:
        sys.exit(1)

    master = UniversalHSQShorMasterEngine(target_M=target)
    master.execute_shor_factorization()
