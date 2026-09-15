# ==============================================================================
# HSQ V6.3 TOPOLOGICAL SHOR MASTER ENGINE (TRUE KICKBACK & SHOTS EDITION)
# Fixed: Directional CPhase Kickback aligned with HSQ V6.0 Spinor Mechanics.
# ==============================================================================

import os
import sys
import time
import math
import secrets
import logging
import json
import hashlib
import platform
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction

import numpy as np
import redis
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import psutil

if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(100000)

logging.getLogger("urllib3").setLevel(logging.ERROR)

SERVER_IP  = os.environ.get("HSQ_SERVER_IP", "127.0.0.1")
BASE_PORT  = int(os.environ.get("HSQ_BASE_PORT", 5011))
REDIS_PORT = int(os.environ.get("TENSOR_BUS_PORT", 2057))

DISCOVERY_TIMEOUT = 8.0
EXECUTION_TIMEOUT = 8.0
MAX_RETRY_COUNT   = 3
MAX_CONCURRENT_WORKERS = 64

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class UniversalHSQShorMasterEngine:
    def __init__(self, target_M: int, target_org: str = "Quantum Evaluation Board", shots: int = 2000, max_trials: int = 10):
        self.M = int(target_M)
        self.target_org = target_org
        self.shots = shots
        self.max_trials = max_trials
        self.L_target = self.M.bit_length()
        self.t_control = 2 * self.L_target
        self.total_nodes_needed = self.t_control + self.L_target
        self.tested_coprimes: Set[int] = set()
        self.start_wall_time = time.time()
        self.trial_history = []

        logging.info("====================================================================")
        logging.info("   HSQ V6.3 SHOR MASTER ENGINE (TRUE KICKBACK & SHOTS)              ")
        logging.info("====================================================================")
        logging.info(f"👉 Target Integer (M) : {self.M}")
        logging.info(f"👉 Reg1 (Control)     : {self.t_control} Nodes")
        logging.info(f"👉 Reg2 (Target)      : {self.L_target} Nodes")
        logging.info(f"👉 Born Rule Shots    : {self.shots} Shots per trial")
        
        try:
            self.redis_bus = redis.Redis(host=SERVER_IP, port=REDIS_PORT, db=0, decode_responses=True, socket_timeout=2.0)
            self.redis_bus.ping()
        except Exception as e:
            logging.error(f"❌ Redis Switch Connection Error: {e}")
            sys.exit(1)

        self.http_session = requests.Session()
        retry_strategy = Retry(total=MAX_RETRY_COUNT, backoff_factor=0.02, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=MAX_CONCURRENT_WORKERS, pool_maxsize=MAX_CONCURRENT_WORKERS, max_retries=retry_strategy)
        self.http_session.mount('http://', adapter)

        self.active_ports = self._discover_hsq_nodes()
        if len(self.active_ports) < self.total_nodes_needed:
            logging.error(f"❌ Active Nodes ({len(self.active_ports)}) < Required ({self.total_nodes_needed})")
            sys.exit(1)

        self.reg1_ports = self.active_ports[:self.t_control]
        self.reg2_ports = self.active_ports[self.t_control:self.total_nodes_needed]
        logging.info(f"✅ HSQ Nodes Ready. Reg1: {self.reg1_ports[0]}~{self.reg1_ports[-1]} | Reg2: {self.reg2_ports[0]}~{self.reg2_ports[-1]}")

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

    def _post_single(self, port: int, endpoint: str, payload: dict) -> Optional[dict]:
        try:
            return self.http_session.post(f"http://{SERVER_IP}:{port}/{endpoint}", json=payload, timeout=EXECUTION_TIMEOUT).json()
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

        all_used_ports = self.reg1_ports + self.reg2_ports
        self._post_parallel(all_used_ports, "reset", lambda i, p: {})
        
        self._post_single(self.reg2_ports[-1], "instruction", {"gate": "x"})
        self._post_parallel(self.reg1_ports, "instruction", lambda i, p: {"gate": "h"})

        # ====================================================================
        # Phase 1: 🌟 修正版 - 物理相位反衝 (True Phase Kickback)
        # ====================================================================
        target_bus = f"hsq_v63_reg2_t{trial_num}"
        # 導出 Reg2 最後一顆 (態為|1>) 的狀態作為相角注入源
        self._post_single(self.reg2_ports[-1], "instruction", {"gate": "export_tensor_metric", "bus_key": target_bus})

        for j, reg1_port in enumerate(self.reg1_ports):
            mod_power = pow(a_generator, 2**j, self.M)
            phase_angle = float((2.0 * np.pi * mod_power) / self.M)

            # 【核心修復】對 Reg1 (Control) 下指令，讓它吃進 Target 的相位！
            self._post_single(reg1_port, "instruction", {
                "gate": "cphase", 
                "delta_phi": phase_angle, 
                "source_bus_key": target_bus
            })

        # ====================================================================
        # Phase 2: 真·逆量子傅立葉變換 (IQFT)
        # ====================================================================
        logging.info("⚛️ Executing True Dynamic IQFT Topology...")
        for i in range(self.t_control - 1, -1, -1):
            port_i = self.reg1_ports[i]
            for j in range(self.t_control - 1, i, -1):
                port_j = self.reg1_ports[j]
                bus_key_j = f"dyn_iqft_q{j}_t{trial_num}"
                
                self._post_single(port_j, "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                iqft_angle = -np.pi / (2 ** (j - i))
                
                # IQFT 內部拓樸：i 被 j 控制。這是正確的方向。
                self._post_single(port_i, "instruction", {"gate": "cphase", "delta_phi": iqft_angle, "source_bus_key": bus_key_j})
            
            self._post_single(port_i, "instruction", {"gate": "h"})

        # ====================================================================
        # Phase 3: 波恩法則 Shots 坍縮統計 (Monte Carlo Sampling)
        # ====================================================================
        probabilities = []
        for port in self.reg1_ports:
            res = self._post_single(port, "instruction", {"gate": "export_tensor_metric", "bus_key": "measure_tmp_v63"})
            if res and "state_b" in res:
                prob_1 = np.clip(res["state_b"][0]**2 + res["state_b"][1]**2, 0.0, 1.0)
                probabilities.append(prob_1)
            else:
                probabilities.append(0.0)

        results_histogram = {}
        rng = secrets.SystemRandom()
        for _ in range(self.shots):
            shot_bits = "".join(["1" if rng.random() < p else "0" for p in probabilities])
            results_histogram[shot_bits] = results_histogram.get(shot_bits, 0) + 1

        top_candidates = sorted(results_histogram.items(), key=lambda x: x[1], reverse=True)[:5]
        
        logging.info(f"🎯 [QPE Measurement] Executed {self.shots} Shots. Top Candidates:")
        for state, count in top_candidates:
            logging.info(f"  ├─ State |{state}> : {count} hits ({count/self.shots*100:.1f}%)")

        # ====================================================================
        # Phase 4: 多重共振峰值週期尋找
        # ====================================================================
        for state, count in top_candidates:
            y_int = int(state, 2)
            theta_phase = y_int / (2**self.t_control)
            if theta_phase == 0.0: continue

            frac = Fraction(theta_phase).limit_denominator(self.M - 1)
            raw_r = frac.denominator
            r_period = self._validate_and_refine_period(a_generator, raw_r)

            if r_period and r_period % 2 == 0:
                half_power = pow(a_generator, r_period // 2, self.M)
                if half_power != self.M - 1 and half_power != 1:
                    factor_1 = math.gcd(half_power - 1, self.M)
                    factor_2 = self.M // factor_1
                    if 1 < factor_1 < self.M:
                        trial_duration = time.time() - trial_start
                        logging.info(f"🏆 [SUCCESS] Target peak |{state}> yielded r={r_period}. Factored {self.M} = {factor_1} * {factor_2}")
                        return "SUCCESS", a_generator, r_period, theta_phase, factor_1, factor_2

        logging.warning("⚠️ All top 5 peaks failed to yield a valid non-trivial factor. Retrying...")
        return "FAILURE_NO_VALID_PEAK", a_generator, None, None, None, None

    def execute_shor_factorization(self):
        for trial in range(1, self.max_trials + 1):
            a_gen = self._get_unique_coprime()
            status, a, r, theta, f1, f2 = self._run_single_quantum_trial(trial, a_gen)
            if status == "SUCCESS":
                break

if __name__ == "__main__":
    print("====================================================================")
    print("===  HSQ V6.3 SHOR FACTORIZATION MASTER (TRUE KICKBACK)          ===")
    print("====================================================================")
    try:
        user_in = input("👉 Enter target integer to factorize (e.g., 15, 35, 43873): ").strip()
        target = int(user_in)
    except Exception:
        sys.exit(1)

    master = UniversalHSQShorMasterEngine(target_M=target, shots=2000)
    master.execute_shor_factorization()
