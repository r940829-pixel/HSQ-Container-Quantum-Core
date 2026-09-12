# ==============================================================================
# HSQ HOLOGRAPHIC QUANTUM FACTORIZER (N = P x Q) [VERSION 6.3]
# [AUTONOMOUS RETRY + PERIOD TOLERANCE & BASE REFINEMENT + COMPOSITE KEY SUPPORT]
# ==============================================================================

import time
import math
import secrets
import logging
from typing import Set, Tuple, Optional
from fractions import Fraction
import numpy as np
import requests

SERVER_IP = "127.0.0.1"
BASE_PORT = 5011
MAX_TRIALS = 50  # 最大自動對焦重試次數

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class HSQHolographicFactorizer:
    def __init__(self, target_N: int = 15):
        self.N = target_N
        self.n_qubits = self.N.bit_length()  # 希爾伯特空間位元數 L
        self.ports = [BASE_PORT + i for i in range(self.n_qubits)]
        self.session = requests.Session()
        self.tested_keys: Set[int] = set()   # 紀錄已測試過的吸引子 Key a

        logging.info("===============================================================")
        logging.info(f"🌀 HSQ HOLOGRAPHIC FACTORIZER V6.3 INITIALIZED FOR N = {self.N}")
        logging.info("===============================================================")
        logging.info(f"👉 Target Integer (N)       : {self.N}")
        logging.info(f"👉 Hilbert Bit-Length       : {self.n_qubits} Qubits")
        logging.info(f"👉 Allocated HSQ Node Ports : {self.ports}")

    def _post(self, port: int, endpoint: str, payload: dict):
        url = f"http://{SERVER_IP}:{port}/{endpoint}"
        try:
            res = self.session.post(url, json=payload, timeout=8.0)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logging.error(f"Node :{port} Communication Error: {e}")
        return None

    def _get_unique_attractor_key(self) -> int:
        """ 隨機抽取全新的吸引子 Key a（允許合數，排除已測試值） """
        while True:
            a_key = secrets.randbelow(self.N - 3) + 2  # 範圍: 2 ~ N-2
            if a_key not in self.tested_keys:
                self.tested_keys.add(a_key)
                return a_key

    def _refine_holographic_period(self, a_key: int, raw_r: int) -> Optional[int]:
        """
        🌟 全息週期容錯與倍數約化核心：
        1. 探測原始週期 raw_r、近鄰偏移 (±1, ±2) 以及小倍數 (1x~4x)
        2. 約化出機能滿足 a^r ≡ 1 (mod N) 的最小基本週期 r_min
        """
        if raw_r <= 0:
            return None

        # Step 1: 探測倍數 m 與近鄰偏移 offset
        found_valid_r = None
        for m in [1, 2, 3, 4]:
            for offset in [0, -1, 1, -2, 2]:
                cand = raw_r * m + offset
                if cand > 0 and pow(a_key, cand, self.N) == 1:
                    found_valid_r = cand
                    break
            if found_valid_r:
                break

        if not found_valid_r:
            return None

        # Step 2: 將有效的週期約化至最小基頻週期 (Base Period Refinement)
        r_min = found_valid_r
        for d in range(1, int(math.isqrt(found_valid_r)) + 1):
            if found_valid_r % d == 0:
                if pow(a_key, d, self.N) == 1:
                    r_min = min(r_min, d)
                other_d = found_valid_r // d
                if pow(a_key, other_d, self.N) == 1:
                    r_min = min(r_min, other_d)

        return r_min

    def _run_single_trial(self, trial_num: int, a_key: int) -> Tuple[str, Optional[int], Optional[int]]:
        logging.info(f"\n====================================================================")
        logging.info(f" 🚀 TRIAL #{trial_num} / {MAX_TRIALS} | Attractor Key a = {a_key}")
        logging.info(f"====================================================================")

        # ----------------------------------------------------------------------
        # 情況 A 預檢：若 a 與 N 不互質，直接觸發 GCD 秒解
        # ----------------------------------------------------------------------
        direct_gcd = math.gcd(a_key, self.N)
        if 1 < direct_gcd < self.N:
            logging.info(f"✨ [Direct GCD Hit] Key a = {a_key} directly shares factor with N!")
            p_cand = direct_gcd
            q_cand = self.N // p_cand
            return "SUCCESS", p_cand, q_cand

        # ----------------------------------------------------------------------
        # 步驟 1: 真空肅清與均勻全息場創始 (Walsh-Hadamard)
        # ----------------------------------------------------------------------
        for port in self.ports:
            self._post(port, "reset", {})
            self._post(port, "instruction", {"gate": "h"})

        # ----------------------------------------------------------------------
        # 步驟 2: 全息相位地圖 (C_map) 鋪設 + 吸引子 Key K 注入
        # ----------------------------------------------------------------------
        for j, port in enumerate(self.ports):
            bus_key = f"hsq_holographic_key_q{j}_t{trial_num}"
            self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key})

            mod_power = pow(a_key, 2**j, self.N)
            c_map_phi = float(2.0 * np.pi * mod_power / self.N)

            self._post(port, "instruction", {
                "gate": "cphase",
                "delta_phi": c_map_phi,
                "source_bus_key": bus_key
            })

        combined_bus_keys = ",".join([f"hsq_holographic_key_q{j}_t{trial_num}" for j in range(self.n_qubits)])
        for port in self.ports:
            self._post(port, "instruction", {
                "gate": "sync_phase_chain",
                "source_bus_key": combined_bus_keys
            })

        # ----------------------------------------------------------------------
        # 步驟 3: 漫步感應 (Quantum Walk Sensing)
        # ----------------------------------------------------------------------
        for port in self.ports:
            self._post(port, "evolve", {"noise": 0.00, "t": 0.1, "grid_size": 500})

        # ----------------------------------------------------------------------
        # 步驟 4: 候選對焦與因數提取 (包含全息週期容錯)
        # ----------------------------------------------------------------------
        measured_bits = []
        for port in self.ports:
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": "measure_harvest"})
            if res and "state_b" in res:
                b_r, b_i = res["state_b"][0], res["state_b"][1]
                prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
                bit = 1 if secrets.SystemRandom().random() < prob_1 else 0
                measured_bits.append(str(bit))
            else:
                measured_bits.append("0")

        bitstring = "".join(measured_bits)
        y_int = int(bitstring, 2)
        theta_phase = y_int / (2 ** self.n_qubits)

        logging.info(f"🎯 Holographic Measurement Bitstring : |{bitstring}>")
        logging.info(f"🔍 Measured Phase Fraction (Theta)   : {theta_phase:.6f}")

        if theta_phase == 0.0:
            logging.warning(" ⚠️ Phase measured as 0.0 (Degenerate state). Auto-retry.")
            return "RETRY_ZERO_PHASE", None, None

        raw_r = Fraction(theta_phase).limit_denominator(self.N - 1).denominator
        logging.info(f"🧮 Raw Extracted Period : r_raw = {raw_r}")

        # 🌟 執行全息週期容錯與約化
        refined_r = self._refine_holographic_period(a_key, raw_r)

        if refined_r is None:
            logging.warning(f" ⚠️ Extracted period {raw_r} failed tolerance validation. Auto-retry.")
            return "RETRY_INVALID_PERIOD", None, None

        logging.info(f"✅ Refined Base Period  : r_true = {refined_r}")

        if refined_r % 2 != 0:
            logging.warning(f" ⚠️ Refined period ({refined_r}) is ODD. Auto-retry.")
            return "RETRY_ODD_PERIOD", None, None

        half_power = pow(a_key, refined_r // 2, self.N)
        if half_power == self.N - 1 or half_power == 1:
            logging.warning(f" ⚠️ Trivial resolution encountered: a^(r/2) ≡ ±1 (mod {self.N}). Auto-retry.")
            return "RETRY_TRIVIAL_SOLUTION", None, None

        p_cand = math.gcd(half_power - 1, self.N)
        q_cand = math.gcd(half_power + 1, self.N)

        if 1 < p_cand < self.N and 1 < q_cand < self.N:
            return "SUCCESS", p_cand, q_cand

        logging.warning(" ⚠️ Extracted factors are trivial. Auto-retry.")
        return "RETRY_TRIVIAL_FACTORS", None, None

    def execute_holographic_factorization(self):
        start_time = time.time()

        for trial in range(1, MAX_TRIALS + 1):
            a_key = self._get_unique_attractor_key()
            status, p_cand, q_cand = self._run_single_trial(trial, a_key)

            if status == "SUCCESS":
                total_time = time.time() - start_time
                logging.info("\n" + "═"*65)
                logging.info(" 🏆 HOLOGRAPHIC FACTORIZATION SUCCESSFUL!")
                logging.info("═"*65)
                logging.info(f" • Target Integer N     : {self.N}")
                logging.info(f" • Factor P' (Candidate): {p_cand}")
                logging.info(f" • Factor Q' (Candidate): {q_cand}")
                logging.info(f" • Verification         : {p_cand} x {q_cand} = {p_cand * q_cand}")
                logging.info(f" • Attractor Key Used   : a = {a_key}")
                logging.info(f" • Total Trials Run     : {trial} Trial(s)")
                logging.info(f" • Total Latency        : {total_time:.3f} Seconds")
                logging.info("═"*65 + "\n")
                return p_cand, q_cand

        logging.error("❌ Exceeded max retry trials without convergence.")
        return None, None

if __name__ == "__main__":
    # 測試 target_N 可以輸入 15, 21, 35 等等
    target = 1147
    factorizer = HSQHolographicFactorizer(target_N=target)
    factorizer.execute_holographic_factorization()
