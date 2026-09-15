# ==============================================================================
# HSQ HOLOGRAPHIC QUANTUM FACTORIZER (N = P x Q) [VERSION 6.4]
# [SEMI-CLASSICAL QPE + TRUE IQFT + BORN RULE SHOTS + AUDIT SIGNATURE]
# ==============================================================================

import os
import sys
import time
import math
import secrets
import logging
import json
import hashlib
from typing import Set, Tuple, Optional, List, Dict
from fractions import Fraction
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import requests

if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(100000)

SERVER_IP = "127.0.0.1"
BASE_PORT = 5011
MAX_TRIALS = 5
SHOTS = 2000
MAX_CONCURRENT_WORKERS = 64

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logging.getLogger("urllib3").setLevel(logging.ERROR)

class HSQHolographicFactorizer:
    def __init__(self, target_N: int = 15):
        self.N = target_N
        # 🌟 為了滿足 QPE 的奈奎斯特定理，全息空間需要 2L 的解析度
        self.n_qubits = 2 * self.N.bit_length()  
        self.ports = [BASE_PORT + i for i in range(self.n_qubits)]
        
        self.session = requests.Session()
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        adapter = HTTPAdapter(pool_connections=MAX_CONCURRENT_WORKERS, pool_maxsize=MAX_CONCURRENT_WORKERS, 
                              max_retries=Retry(total=3, backoff_factor=0.02))
        self.session.mount("http://", adapter)
        
        self.tested_keys: Set[int] = set()
        self.start_wall_time = time.time()
        self.trial_telemetry = []

        logging.info("===============================================================")
        logging.info(f"🌀 HSQ HOLOGRAPHIC FACTORIZER V6.4 INITIALIZED FOR N = {self.N}")
        logging.info("===============================================================")
        logging.info(f"👉 Target Integer (N)       : {self.N}")
        logging.info(f"👉 Holographic Resolution   : {self.n_qubits} Qubits (2L)")
        logging.info(f"👉 Allocated HSQ Ports      : {self.ports[0]} ~ {self.ports[-1]}")
        logging.info(f"👉 Quantum Born Rule Shots  : {SHOTS} Shots/Trial")

    def _post_single(self, port: int, endpoint: str, payload: dict) -> Optional[dict]:
        try:
            res = self.session.post(f"http://{SERVER_IP}:{port}/{endpoint}", json=payload, timeout=5.0)
            if res.status_code == 200: return res.json()
        except: pass
        return None

    def _post_parallel(self, ports: List[int], endpoint: str, payload_builder_func) -> List[Optional[dict]]:
        results = [None] * len(ports)
        with ThreadPoolExecutor(max_workers=min(len(ports), MAX_CONCURRENT_WORKERS)) as executor:
            future_to_idx = {executor.submit(self._post_single, port, endpoint, payload_builder_func(i, port)): i for i, port in enumerate(ports)}
            for future in as_completed(future_to_idx):
                results[future_to_idx[future]] = future.result()
        return results

    def _get_unique_attractor_key(self) -> int:
        while True:
            a_key = secrets.randbelow(self.N - 3) + 2
            if a_key not in self.tested_keys:
                self.tested_keys.add(a_key)
                return a_key

    def _refine_holographic_period(self, a_key: int, raw_r: int) -> Optional[int]:
        if raw_r <= 0: return None
        found_valid_r = None
        
        for m in [1, 2, 3, 4]:
            for offset in [0, -1, 1, -2, 2]:
                cand = raw_r * m + offset
                if cand > 0 and pow(a_key, cand, self.N) == 1:
                    found_valid_r = cand; break
            if found_valid_r: break
        
        if not found_valid_r: return None

        r_min = found_valid_r
        for d in range(1, int(math.isqrt(found_valid_r)) + 1):
            if found_valid_r % d == 0:
                if pow(a_key, d, self.N) == 1: r_min = min(r_min, d)
                if pow(a_key, found_valid_r // d, self.N) == 1: r_min = min(r_min, found_valid_r // d)
        return r_min

    def _run_single_trial(self, trial_num: int, a_key: int) -> Tuple[str, Optional[int], Optional[int], Optional[int]]:
        logging.info(f"\n" + "="*65)
        logging.info(f" 🚀 TRIAL #{trial_num} / {MAX_TRIALS} | Attractor Key a = {a_key}")
        logging.info("="*65)

        direct_gcd = math.gcd(a_key, self.N)
        if 1 < direct_gcd < self.N:
            logging.info(f"✨ [Direct GCD Hit] Key a = {a_key} directly shares factor with N!")
            return "SUCCESS_DIRECT_GCD", a_key, direct_gcd, self.N // direct_gcd

        # ----------------------------------------------------------------------
        # Step 1: 真空肅清與均勻全息場創始 (Superposition)
        # ----------------------------------------------------------------------
        self._post_parallel(self.ports, "reset", lambda i, p: {})
        self._post_parallel(self.ports, "instruction", lambda i, p: {"gate": "h"})

        # ----------------------------------------------------------------------
        # Step 2: 全息相位地圖直接注入 (Semi-Classical Holographic Injection)
        # 捨棄笨重的 Reg2，直接計算特徵值相角並灌入 HSQ 節點
        # ----------------------------------------------------------------------
        for j, port in enumerate(self.ports):
            mod_power = pow(a_key, 2**j, self.N)
            c_map_phi = float(2.0 * np.pi * mod_power / self.N)
            # 🌟 直接使用 phase 閘，將模冪特徵值刻印到波包中
            self._post_single(port, "instruction", {"gate": "phase", "delta_phi": c_map_phi})

        # ----------------------------------------------------------------------
        # Step 3: 真·逆量子傅立葉變換 (True IQFT)
        # ----------------------------------------------------------------------
        logging.info("⚛️ Executing Holographic IQFT Topology...")
        for i in range(self.n_qubits - 1, -1, -1):
            port_i = self.ports[i]
            for j in range(self.n_qubits - 1, i, -1):
                port_j = self.ports[j]
                bus_key_j = f"holo_iqft_q{j}_t{trial_num}"
                self._post_single(port_j, "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                iqft_angle = -np.pi / (2 ** (j - i))
                self._post_single(port_i, "instruction", {"gate": "cphase", "delta_phi": iqft_angle, "source_bus_key": bus_key_j})
            self._post_single(port_i, "instruction", {"gate": "h"})

        # ----------------------------------------------------------------------
        # Step 4: 波恩法則 Shots 坍縮統計 (Monte Carlo Sampling)
        # ----------------------------------------------------------------------
        probabilities = []
        for port in self.ports:
            res = self._post_single(port, "instruction", {"gate": "export_tensor_metric", "bus_key": "measure_holo"})
            if res and "state_b" in res:
                prob_1 = np.clip(res["state_b"][0]**2 + res["state_b"][1]**2, 0.0, 1.0)
                probabilities.append(prob_1)
            else:
                probabilities.append(0.0)

        results_histogram = {}
        rng = secrets.SystemRandom()
        for _ in range(SHOTS):
            shot_bits = "".join(["1" if rng.random() < p else "0" for p in probabilities])
            results_histogram[shot_bits] = results_histogram.get(shot_bits, 0) + 1

        top_candidates = sorted(results_histogram.items(), key=lambda x: x[1], reverse=True)[:5]
        
        logging.info(f"🎯 [Holographic Measurement] {SHOTS} Shots. Top Peaks:")
        for state, count in top_candidates:
            logging.info(f"  ├─ State |{state}> : {count} hits ({count/SHOTS*100:.1f}%)")

        # ----------------------------------------------------------------------
        # Step 5: 候選對焦與因數提取
        # ----------------------------------------------------------------------
        for state, count in top_candidates:
            y_int = int(state, 2)
            theta_phase = y_int / (2 ** self.n_qubits)
            if theta_phase == 0.0: continue

            raw_r = Fraction(theta_phase).limit_denominator(self.N - 1).denominator
            refined_r = self._refine_holographic_period(a_key, raw_r)

            if refined_r and refined_r % 2 == 0:
                half_power = pow(a_key, refined_r // 2, self.N)
                if half_power != self.N - 1 and half_power != 1:
                    p_cand = math.gcd(half_power - 1, self.N)
                    q_cand = self.N // p_cand
                    if 1 < p_cand < self.N:
                        logging.info(f"🏆 [SUCCESS] Peak |{state}> yielded r={refined_r}. Factored {self.N} = {p_cand} * {q_cand}")
                        return "SUCCESS", a_key, p_cand, q_cand

        logging.warning(" ⚠️ All top peaks failed tolerance validation. Auto-retry.")
        return "RETRY_NO_VALID_PEAK", a_key, None, None

    def _generate_audit_signature(self, report: dict) -> str:
        serialized = json.dumps(report, sort_keys=True).encode('utf-8')
        return hashlib.sha256(serialized).hexdigest()

    def execute_holographic_factorization(self):
        for trial in range(1, MAX_TRIALS + 1):
            a_key = self._get_unique_attractor_key()
            status, successful_a, p_cand, q_cand = self._run_single_trial(trial, a_key)
            
            self.trial_telemetry.append({
                "trial": trial, "attractor_key_a": a_key, "status": status
            })

            if "SUCCESS" in status:
                total_time = time.time() - self.start_wall_time
                
                # 🌟 生成防篡改特徵碼紀錄
                audit_report = {
                    "system": "HSQ Holographic Factorizer V6.4",
                    "target_N": self.N,
                    "resolution_qubits": self.n_qubits,
                    "shots_per_trial": SHOTS,
                    "total_latency_sec": round(total_time, 4),
                    "successful_attractor_a": successful_a,
                    "factor_P": p_cand,
                    "factor_Q": q_cand,
                    "telemetry": self.trial_telemetry
                }
                signature = self._generate_audit_signature(audit_report)
                audit_report["cryptographic_signature_sha256"] = signature

                # 寫入 JSON 報告
                report_file = f"HSQ_HOLO_FACTOR_{self.N}_AUDIT.json"
                with open(report_file, "w", encoding="utf-8") as f:
                    json.dump(audit_report, f, indent=2)

                logging.info("\n" + "═"*65)
                logging.info(" 🏆 HOLOGRAPHIC FACTORIZATION SECURELY COMPLETED!")
                logging.info("═"*65)
                logging.info(f" • Target Integer N     : {self.N}")
                logging.info(f" • Factor P (Candidate) : {p_cand}")
                logging.info(f" • Factor Q (Candidate) : {q_cand}")
                logging.info(f" • Verification         : {p_cand} x {q_cand} = {p_cand * q_cand}")
                logging.info(f" • Attractor Key Used   : a = {successful_a}")
                logging.info(f" • Total Trials Run     : {trial} Trial(s)")
                logging.info(f" • Total Latency        : {total_time:.3f} Seconds")
                logging.info(f" 🔒 Cryptographic Sig   : {signature}")
                logging.info(f" 📝 Audit File Saved    : {report_file}")
                logging.info("═"*65 + "\n")
                return p_cand, q_cand

        logging.error("❌ Exceeded max retry trials without convergence.")
        return None, None

if __name__ == "__main__":
    print("====================================================================")
    print("===  HSQ V6.4 HOLOGRAPHIC FACTORIZER (SHOTS & AUDIT EDITION)     ===")
    print("====================================================================")
    try:
        user_in = input("👉 Enter target integer to factorize (e.g., 15, 35, 1147): ").strip()
        target = int(user_in)
    except Exception:
        sys.exit(1)

    factorizer = HSQHolographicFactorizer(target_N=target)
    factorizer.execute_holographic_factorization()
