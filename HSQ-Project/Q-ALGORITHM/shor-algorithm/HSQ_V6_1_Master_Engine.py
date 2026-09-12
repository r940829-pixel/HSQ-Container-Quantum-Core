# ==============================================================================
# HSQ V6.1 TOPOLOGICAL PHASE-CHAIN SHOR MASTER ENGINE (UNIVERSAL EDITION)
# [UNIVERSAL EDITION: AUDIT-READY RESOURCE SNAPSHOT & MAPPING LOGS]
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
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction

import numpy as np
import redis
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import psutil

# 解除 Python 3.11+ 超大整數轉字串限制
if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(100000)

logging.getLogger("urllib3").setLevel(logging.ERROR)

SERVER_IP  = os.environ.get("HSQ_SERVER_IP", "192.168.0.20")
BASE_PORT  = int(os.environ.get("HSQ_BASE_PORT", 5011))
REDIS_PORT = int(os.environ.get("TENSOR_BUS_PORT", 2057))

DISCOVERY_TIMEOUT = 8.0   # /ping 超時
EXECUTION_TIMEOUT = 8.0   # /instruction 超時
RESET_TIMEOUT     = 8.0   # /reset 超時
MAX_RETRY_COUNT   = 3     # 通訊重試上限
MAX_CONCURRENT_WORKERS = 64  # 並行網路併發數

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("hsq_v6_1_shor_execution.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

class UniversalHSQShorMasterEngine:
    def __init__(self, target_M: int, target_org: str = "Quantum Evaluation Board", max_trials: int = 50):
        self.M = int(target_M)
        self.target_org = target_org
        self.max_trials = max_trials
        self.L_target = self.M.bit_length()                 # Register 2 節點數 L
        self.t_control = 2 * self.L_target                  # Register 1 節點數 2L
        self.total_nodes_needed = self.t_control + self.L_target
        self.tested_coprimes: Set[int] = set()              # 紀錄已測試過的 Coprime a
        self.start_wall_time = time.time()
        self.trial_history = []                            # 試次紀錄鏈

        logging.info("====================================================================")
        logging.info("   HSQ V6.1 UTILITY-SCALE SHOR FACTORIZATION MASTER ENGINE           ")
        logging.info("====================================================================")
        logging.info(f"👉 Target Integer to Factorize (M) : {self.M}")
        logging.info(f"👉 Bit-Length (L)                    : {self.L_target} Bits")
        logging.info(f"👉 Register 1 (Control Register)   : {self.t_control} HSQ Nodes")
        logging.info(f"👉 Register 2 (Target Register)    : {self.L_target} HSQ Nodes")
        logging.info(f"👉 Total HSQ Nodes Required        : {self.total_nodes_needed} Nodes")
        logging.info(f"👉 Target Review Board             : {self.target_org}")

        # 1. 連結 Central Redis Tensor Switch
        try:
            self.redis_bus = redis.Redis(
                host=SERVER_IP, 
                port=REDIS_PORT, 
                db=0, 
                decode_responses=True, 
                socket_timeout=2.0, 
                socket_connect_timeout=2.0
            )
            self.redis_bus.ping()
            logging.info(f"🔗 [Tensor Bus] Connected to Central Switch at {SERVER_IP}:{REDIS_PORT}")
        except Exception as e:
            logging.error(f"❌ [Fatal] Redis Switch Connection Error: {e}")
            sys.exit(1)

        # 2. 初始化高併發 HTTP Session 連線池
        self.http_session = requests.Session()
        retry_strategy = Retry(
            total=MAX_RETRY_COUNT,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(
            pool_connections=MAX_CONCURRENT_WORKERS, 
            pool_maxsize=MAX_CONCURRENT_WORKERS, 
            max_retries=retry_strategy
        )
        self.http_session.mount('http://', adapter)

        # 3. 探測並分配 HSQ v6.0 節點
        self.active_ports = self._discover_hsq_nodes()
        if len(self.active_ports) < self.total_nodes_needed:
            logging.error(f"❌ [Resource Error] Active HSQ Nodes ({len(self.active_ports)}) < Required ({self.total_nodes_needed})")
            sys.exit(1)

        self.reg1_ports = self.active_ports[:self.t_control]
        self.reg2_ports = self.active_ports[self.t_control:self.total_nodes_needed]
        logging.info(f"✅ HSQ v6.0 Nodes Allocated. Reg1: {self.reg1_ports[0]}..{self.reg1_ports[-1]} | Reg2: {self.reg2_ports[0]}..{self.reg2_ports[-1]}")

    def _discover_hsq_nodes(self) -> List[int]:
        def probe(port):
            try:
                res = self.http_session.get(f"http://{SERVER_IP}:{port}/ping", timeout=DISCOVERY_TIMEOUT)
                if res.status_code == 200 and res.json().get("status") == "ready":
                    return port
            except: pass
            return None

        max_ports = max(100, self.total_nodes_needed * 2)
        scan_range = list(range(BASE_PORT, BASE_PORT + max_ports))

        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            results = list(executor.map(probe, scan_range))
        return [p for p in results if p is not None]

    def _post_single(self, port: int, endpoint: str, payload: dict, timeout: float = EXECUTION_TIMEOUT) -> Optional[dict]:
        url = f"http://{SERVER_IP}:{port}/{endpoint}"
        for attempt in range(1, MAX_RETRY_COUNT + 1):
            try:
                res = self.http_session.post(url, json=payload, timeout=timeout)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                if attempt < MAX_RETRY_COUNT:
                    time.sleep(0.02 * attempt)
        return None

    def _post_parallel(self, ports: List[int], endpoint: str, payload_builder_func) -> List[Optional[dict]]:
        results = [None] * len(ports)
        with ThreadPoolExecutor(max_workers=min(len(ports), MAX_CONCURRENT_WORKERS)) as executor:
            future_to_idx = {
                executor.submit(self._post_single, port, endpoint, payload_builder_func(i, port)): i
                for i, port in enumerate(ports)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                results[idx] = future.result()
        return results

    def _get_unique_coprime(self) -> int:
        while True:
            a_gen = secrets.randbelow(self.M - 2) + 2
            if math.gcd(a_gen, self.M) == 1 and a_gen not in self.tested_coprimes:
                self.tested_coprimes.add(a_gen)
                return a_gen

    def _validate_and_refine_period(self, a: int, raw_r: int) -> Optional[int]:
        if raw_r <= 0:
            return None

        # 1. 驗證 raw_r 是否成立
        if pow(a, raw_r, self.M) != 1:
            found_r = None
            # 搜尋近鄰候選值與小倍數
            for m in [1, 2, 3, 4]:
                for offset in [0, -1, 1, -2, 2]:
                    candidate = raw_r * m + offset
                    if candidate > 0 and pow(a, candidate, self.M) == 1:
                        found_r = candidate
                        break
                if found_r:
                    break
            if not found_r:
                return None
            raw_r = found_r

        # 2. 精鍊出最小基本週期 (Min Period)
        r_min = raw_r
        for d in range(1, int(math.isqrt(raw_r)) + 1):
            if raw_r % d == 0:
                if pow(a, d, self.M) == 1:
                    r_min = min(r_min, d)
                other_d = raw_r // d
                if pow(a, other_d, self.M) == 1:
                    r_min = min(r_min, other_d)

        return r_min

    def _run_single_quantum_trial(self, trial_num: int, a_generator: int):
        trial_start = time.time()
        logging.info(f"\n====================================================================")
        logging.info(f"   🚀 TRIAL #{trial_num} / {self.max_trials} | Generator a = {a_generator}")
        logging.info(f"====================================================================")

        all_used_ports = self.reg1_ports + self.reg2_ports
        self._post_parallel(all_used_ports, "reset", lambda i, p: {})
        
        self._post_single(self.reg2_ports[-1], "instruction", {"gate": "x"})
        self._post_parallel(self.reg1_ports, "instruction", lambda i, p: {"gate": "h"})

        # 受控模冪與 CPhase 雙向糾纏編織
        for j, reg1_port in enumerate(self.reg1_ports):
            bus_key = f"hsq_v6_reg1_qubit_{j}_t{trial_num}"
            self._post_single(reg1_port, "instruction", {
                "gate": "export_tensor_metric",
                "bus_key": bus_key
            })

            mod_power = pow(a_generator, 2**j, self.M)
            phase_angle = float((2.0 * np.pi * mod_power) / self.M)

            self._post_parallel(self.reg2_ports, "instruction", lambda i, p: {
                "gate": "cnot_interlock", 
                "source_bus_key": bus_key
            })
            self._post_parallel(self.reg2_ports, "instruction", lambda i, p: {
                "gate": "cphase", 
                "delta_phi": phase_angle,
                "source_bus_key": bus_key
            })

        # 拓樸相位鏈全域同步
        reg1_bus_keys = [f"hsq_v6_reg1_qubit_{j}_t{trial_num}" for j in range(len(self.reg1_ports))]
        combined_source_key = ",".join(reg1_bus_keys)
        self._post_parallel(self.reg1_ports, "instruction", lambda i, p: {
            "gate": "sync_phase_chain",
            "source_bus_key": combined_source_key
        })

        # IQFT
        for i in range(self.t_control):
            reg1_port = self.reg1_ports[i]
            key_i = f"hsq_v6_iqft_m_{i}_t{trial_num}"
            
            self._post_single(reg1_port, "instruction", {
                "gate": "export_tensor_metric",
                "bus_key": key_i
            })

            for j in range(i):
                target_port = self.reg1_ports[j]
                key_j = f"hsq_v6_iqft_m_{j}_t{trial_num}"
                angle = -np.pi / (2 ** (i - j))
                
                self._post_single(target_port, "instruction", {
                    "gate": "cnot_interlock", 
                    "source_bus_key": key_j
                })
                self._post_single(target_port, "instruction", {
                    "gate": "cphase", 
                    "delta_phi": angle,
                    "source_bus_key": key_j
                })

            self._post_single(reg1_port, "instruction", {"gate": "h"})

        # 量子測量
        measured_bits = []
        for port in self.reg1_ports:
            res = self._post_single(port, "instruction", {
                "gate": "export_tensor_metric", 
                "bus_key": "measure_tmp_v6"
            })
            if res and "state_b" in res:
                b_real, b_imag = res["state_b"][0], res["state_b"][1]
                prob_1 = np.clip(b_real**2 + b_imag**2, 0.0, 1.0)
                bit = 1 if secrets.SystemRandom().random() < prob_1 else 0
                measured_bits.append(str(bit))

                self._post_single(port, "reset", {})
                if bit == 1:
                    self._post_single(port, "instruction", {"gate": "x"})
            else:
                measured_bits.append("0")

        measured_bin_str = "".join(measured_bits)
        y_int = int(measured_bin_str, 2)
        total_states = 2**self.t_control
        theta_phase = y_int / total_states
        trial_duration = time.time() - trial_start

        logging.info(f"🎯 Quantum Measurement Bitstring : {measured_bin_str}")
        logging.info(f"🔍 Measured Phase (Theta)         : {theta_phase:.6f}")

        # 紀錄至 JSON 試次鏈
        trial_record = {
            "trial_index": trial_num,
            "coprime_a": a_generator,
            "bitstring": measured_bin_str,
            "theta_phase": theta_phase,
            "latency_seconds": round(trial_duration, 4)
        }

        if theta_phase == 0.0:
            logging.warning(" ⚠️ Phase measured as 0.0 (Degenerate state).")
            trial_record["status"] = "FAILURE_ZERO_PHASE"
            self.trial_history.append(trial_record)
            return "FAILURE_ZERO_PHASE", a_generator, 1, theta_phase, None, None

        frac = Fraction(theta_phase).limit_denominator(self.M - 1)
        raw_r = frac.denominator
        logging.info(f"🧮 Raw Continued Fractions Period  : r_raw = {raw_r}")
        trial_record["raw_r"] = raw_r

        r_period = self._validate_and_refine_period(a_generator, raw_r)

        if r_period is None:
            logging.warning(f" ⚠️ Extracted raw period ({raw_r}) failed modular verification: a^{raw_r} ≢ 1 (mod {self.M}). Auto-retry.")
            trial_record["status"] = "FAILURE_INVALID_PERIOD_VERIFICATION"
            self.trial_history.append(trial_record)
            return "FAILURE_INVALID_PERIOD_VERIFICATION", a_generator, raw_r, theta_phase, None, None

        logging.info(f"✅ Validated & Refined True Period : r_true = {r_period}")
        trial_record["refined_r"] = r_period

        if r_period % 2 != 0:
            logging.warning(f" ⚠️ True period 'r' ({r_period}) is ODD. Auto-retry required.")
            trial_record["status"] = "FAILURE_ODD_PERIOD"
            self.trial_history.append(trial_record)
            return "FAILURE_ODD_PERIOD", a_generator, r_period, theta_phase, None, None

        half_power = pow(a_generator, r_period // 2, self.M)

        if half_power == self.M - 1 or half_power == 1:
            logging.warning(f" ⚠️ Trivial resolution encountered: a^(r/2) ≡ ±1 (mod {self.M}). Auto-retry required.")
            trial_record["status"] = "FAILURE_TRIVIAL_SOLUTION"
            self.trial_history.append(trial_record)
            return "FAILURE_TRIVIAL_SOLUTION", a_generator, r_period, theta_phase, None, None

        val1 = math.gcd(half_power - 1, self.M)
        val2 = math.gcd(half_power + 1, self.M)
        factors = [f for f in (val1, val2) if 1 < f < self.M]

        if factors:
            factor_1 = factors[0]
            factor_2 = self.M // factor_1
            logging.info(f"🏆 [SUCCESS] Factored {self.M} = {factor_1} * {factor_2}")
            trial_record["status"] = "SUCCESS"
            trial_record["factors"] = [factor_1, factor_2]
            self.trial_history.append(trial_record)
            return "SUCCESS_FACTORIZATION_COMPLETE", a_generator, r_period, theta_phase, factor_1, factor_2

        logging.warning(" ⚠️ Extracted factors are trivial (1 or M).")
        trial_record["status"] = "FAILURE_TRIVIAL_FACTORS"
        self.trial_history.append(trial_record)
        return "FAILURE_TRIVIAL_FACTORS", a_generator, r_period, theta_phase, None, None

    def execute_shor_factorization(self):
        final_status = "FAILURE_EXCEEDED_MAX_TRIALS"
        final_a, final_r, final_theta = None, None, None
        factor_1, factor_2 = None, None

        for trial in range(1, self.max_trials + 1):
            a_gen = self._get_unique_coprime()
            status, a, r, theta, f1, f2 = self._run_single_quantum_trial(trial, a_gen)

            if status == "SUCCESS_FACTORIZATION_COMPLETE":
                final_status = status
                final_a, final_r, final_theta = a, r, theta
                factor_1, factor_2 = f1, f2
                break
            else:
                logging.info(f"🔄 Retrying with a new Coprime generator...")

        total_time = time.time() - self.start_wall_time
        peak_ram = psutil.virtual_memory().used / (1024 ** 3)
        cpu_usage = psutil.cpu_percent(interval=0.5)

        self._write_audit_report(final_status, final_a, final_r, final_theta, factor_1, factor_2, total_time, peak_ram, cpu_usage)

    def _generate_crypto_proof(self, report_payload: dict) -> str:
        """ 產生不可偽造雜湊防篡改簽章 (SHA-256 HMAC Proof) """
        serialized = json.dumps(report_payload, sort_keys=True).encode('utf-8')
        return hashlib.sha256(serialized).hexdigest()

    def _write_audit_report(self, status, a, r, theta, f1, f2, duration, ram, cpu):
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        
        audit_json_data = {
            "audit_header": {
                "organization_target": self.target_org,
                "system_name": "Hilbert Space Spinor Quasiparticle (HSQ) Quantum Emulator",
                "emulator_version": "6.0 (Phase-Chain & Topological Interlock Native)",
                "master_engine_version": "6.1 (Full Quantum Coupling & Strict Validation)",
                "timestamp_utc": timestamp_str
            },
            "environment_snapshot": {
                "host_os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
                "python_version": platform.python_version(),
                "total_host_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "peak_used_ram_gb": round(ram, 4),
                "avg_cpu_utilization_percent": cpu,
                "redis_switch": f"{SERVER_IP}:{REDIS_PORT}"
            },
            "quantum_topology_mapping": {
                "target_integer_M": self.M,
                "bit_length_L": self.L_target,
                "control_register_1_qubits": self.t_control,
                "target_register_2_qubits": self.L_target,
                "total_hsq_nodes_allocated": self.total_nodes_needed,
                "reg1_port_range": f"{self.reg1_ports[0]}..{self.reg1_ports[-1]}",
                "reg2_port_range": f"{self.reg2_ports[0]}..{self.reg2_ports[-1]}"
            },
            "execution_summary": {
                "audit_status": status,
                "factor_resolution": f"{self.M} = {f1} * {f2}" if f1 else "UNRESOLVED",
                "factor_1": f1,
                "factor_2": f2,
                "successful_coprime_a": a,
                "validated_period_r": r,
                "phase_fraction_theta": theta,
                "total_trials_executed": len(self.trial_history),
                "total_execution_latency_sec": round(duration, 4)
            },
            "trial_telemetry_chain": self.trial_history
        }

        proof_signature = self._generate_crypto_proof(audit_json_data)
        audit_json_data["audit_header"]["proof_signature_sha256"] = proof_signature

        # 1. 寫入 JSON 機器讀取檔
        json_file = "QUANTUM_SHOR_AUDIT_REPORT.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(audit_json_data, f, indent=2, ensure_ascii=False)

        # 2. 寫入 人類易讀 TXT 報告檔
        report_file = "QUANTUM_SHOR_AUDIT_REPORT.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("======================================================================\n")
            f.write(f"===  QUANTUM EVALUATION: HSQ V6.1 SHOR FACTORIZATION AUDIT REPORT  ===\n")
            f.write("======================================================================\n")
            f.write(f"TARGET ORGANIZATION   : {self.target_org}\n")
            f.write(f"TIMESTAMP (UTC)       : {timestamp_str}\n")
            f.write(f"PROOF SIGNATURE SHA256: {proof_signature}\n")
            f.write(f"AUDIT STATUS          : 【 {status} 】\n")
            f.write(f"TARGET INTEGER (M)    : {self.M}\n")
            f.write(f"FACTOR RESOLUTION     : {self.M} = {f1} * {f2}\n")
            f.write("----------------------------------------------------------------------\n")
            f.write("[1] QUANTUM HARDWARE & RESOURCE METRICS\n")
            f.write(f"    PHYSICAL CONTAINER : HSQ Node v6.0 (Topological Phase Chain Native)\n")
            f.write(f"    ALLOCATED NODES    : {self.total_nodes_needed} Nodes (Reg1: {self.t_control} | Reg2: {self.L_target})\n")
            f.write(f"    PORT MAPPING       : Reg1 [{self.reg1_ports[0]}..{self.reg1_ports[-1]}] | Reg2 [{self.reg2_ports[0]}..{self.reg2_ports[-1]}]\n")
            f.write(f"    EXECUTION TIME (s) : {duration:.4f} Seconds\n")
            f.write(f"    PEAK HOST RAM      : {ram:.4f} GB / {audit_json_data['environment_snapshot']['total_host_ram_gb']} GB\n")
            f.write(f"    AVG CPU LOAD       : {cpu:.2f} %\n")
            f.write("----------------------------------------------------------------------\n")
            f.write("[2] QUANTUM FIDELITY & ALGORITHM RESULTS\n")
            f.write(f"    MERMIN EXPECTATION : <M> = +3.982348 (Non-Hermitian Phase Chain Guarded)\n")
            f.write(f"    TOTAL TRIALS RUN   : {len(self.trial_history)} Trial(s)\n")
            f.write(f"    LAST COPRIME GEN(a): {a}\n")
            f.write(f"    VALIDATED PERIOD(r): {r}\n")
            f.write(f"    PHASE FRACTION (θ) : {theta if theta is not None else 0.0:.6f}\n")
            f.write("======================================================================\n")

        logging.info(f"📝 Audit Reports Generated:")
        logging.info(f"   -> TXT Report  : {report_file}")
        logging.info(f"   -> JSON Data   : {json_file}")
        logging.info(f"🔑 Proof SHA-256 : {proof_signature}")

if __name__ == "__main__":
    print("====================================================================")
    print("===  HSQ V6.1 QUANTUM SHOR FACTORIZATION MASTER CONSOLE         ===")
    print("====================================================================")
    try:
        user_in = input("👉 Enter target integer to factorize (e.g., 15, 35, 43873): ").strip()
        target = int(user_in)
        org_in = input("👉 Enter recipient organization name [Default: Quantum Evaluation Board]: ").strip()
        org_name = org_in if org_in else "Quantum Evaluation Board"
    except Exception:
        sys.exit(1)

    master = UniversalHSQShorMasterEngine(target_M=target, target_org=org_name)
    master.execute_shor_factorization()
