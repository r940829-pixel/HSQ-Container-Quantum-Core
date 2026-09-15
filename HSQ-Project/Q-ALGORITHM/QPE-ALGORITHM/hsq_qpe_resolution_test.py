# ==============================================================================
# HOLOGRAPHIC QUANTUM PHASE ESTIMATION (QPE) ENGINE [DYNAMIC RESOLUTION EDITION]
# Dynamic Control Nodes Generation | True Quantum Shots Statistics
# ==============================================================================

import time
import numpy as np
import requests
import secrets
from typing import List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SERVER_IP = "127.0.0.1"
BASE_PORT = 5011

class HsqDynamicQpeEngine:
    def __init__(self, num_controls: int = 5, target_theta: float = 0.321, shots: int = 1000):
        self.num_controls = num_controls
        self.theta = target_theta
        self.shots = shots
        
        # 動態分配 Ports：Q0 ~ Q(n-1) 為 Control，最後一顆為 Target
        self.control_ports = [BASE_PORT + i for i in range(self.num_controls)]
        self.target_port = BASE_PORT + self.num_controls
        self.all_ports = self.control_ports + [self.target_port]

        # 建立高併發 HTTP 連線池 (參考 Diffusion 腳本架構)
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3, backoff_factor=0.02,
            status_forcelist=[500, 502, 503, 504], raise_on_status=False
        )
        adapter = HTTPAdapter(pool_connections=64, pool_maxsize=64, max_retries=retry_strategy)
        self.session.mount("http://", adapter)

    def _post(self, port: int, endpoint: str, payload: dict = None) -> dict:
        url = f"http://{SERVER_IP}:{port}/{endpoint}"
        return self.session.post(url, json=payload or {}, timeout=5.0).json()

    def run_dynamic_qpe(self):
        print("======================================================================")
        print(f"⚛️  [Dynamic QPE] 啟動量子相位估計")
        print(f"  ├─ 目標相角 (θ)  : {self.theta}")
        print(f"  ├─ Control 節點  : {self.num_controls} 顆 (Ports: {self.control_ports[0]}~{self.control_ports[-1]})")
        print(f"  ├─ Target  節點  : 1 顆 (Port: {self.target_port})")
        print(f"  └─ 理論解析度    : 1 / {2**self.num_controls} = {1/(2**self.num_controls):.6f}")
        print("======================================================================\n")

        # Step 0: 系統重置
        for port in self.all_ports:
            self._post(port, "reset")

        # Step 1: 狀態準備
        self._post(self.target_port, "instruction", {"gate": "x"})
        target_bus = "dyn_qpe_target"
        self._post(self.target_port, "instruction", {"gate": "export_tensor_metric", "bus_key": target_bus})
        
        for port in self.control_ports:
            self._post(port, "instruction", {"gate": "h"})

        # Step 2: 動態 Phase Kickback 注入
        target_phase_angle = 2.0 * np.pi * self.theta
        for j, control_port in enumerate(self.control_ports):
            kickback_angle = target_phase_angle * (2 ** j)
            self._post(control_port, "instruction", {
                "gate": "cphase",
                "delta_phi": kickback_angle,
                "source_bus_key": target_bus
            })
        print("✅ 非定域相位反彈 (Phase Kickback) 矩陣注入完成。")

        # Step 3: 動態 Inverse QFT (IQFT)
        for i in range(self.num_controls - 1, -1, -1):
            port_i = self.control_ports[i]
            for j in range(self.num_controls - 1, i, -1):
                port_j = self.control_ports[j]
                bus_key_j = f"dyn_iqft_q{j}"
                
                self._post(port_j, "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                iqft_angle = -np.pi / (2 ** (j - i))
                self._post(port_i, "instruction", {
                    "gate": "cphase",
                    "delta_phi": iqft_angle,
                    "source_bus_key": bus_key_j
                })
            self._post(port_i, "instruction", {"gate": "h"})
        print("✅ 逆量子傅立葉變換 (IQFT) 拓樸干涉完成。\n")

        # Step 4: 擷取隱藏振幅與 Shots 坍縮統計
        probabilities = []
        for i, port in enumerate(self.control_ports):
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"dyn_final_q{i}"})
            b_r, b_i = res["state_b"][0], res["state_b"][1]
            prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
            probabilities.append(prob_1)

        # 輸出微觀振幅
        prob_str = " | ".join([f"Q{i}:{p:.4f}" for i, p in enumerate(probabilities)])
        print(f"📊 [Statevector 隱藏振幅] {prob_str}")

        # 執行蒙地卡羅坍縮
        results_histogram = {}
        rng = secrets.SystemRandom()
        for _ in range(self.shots):
            shot_bits = "".join(["1" if rng.random() < p else "0" for p in probabilities])
            results_histogram[shot_bits] = results_histogram.get(shot_bits, 0) + 1

        # 解析統計結果
        best_state = max(results_histogram, key=results_histogram.get)
        decimal_val = int(best_state, 2) / (2 ** self.num_controls)

        print(f"\n🎯 [QPE Measurement] 執行 {self.shots} 次 Shots 統計結果 (Top 5):")
        for state, count in sorted(results_histogram.items(), key=lambda x: x[1], reverse=True)[:5]:
            val = int(state, 2) / (2 ** self.num_controls)
            print(f"  ├─ 狀態 |{state}> : {count:4d} 次 ({(count/self.shots)*100:5.1f}%) => 數值: {val:.5f}")

        print("\n======================================================================")
        print(f"✨ 目標真實相角 (θ) : {self.theta}")
        print(f"✨ 統計最高頻狀態   : 0.{best_state} (二進位)")
        print(f"✨ 推導相位數值     : {decimal_val:.6f}")
        print(f"✨ 絕對誤差 (Error) : {abs(self.theta - decimal_val):.6f}")
        print("======================================================================")

if __name__ == "__main__":
    # 可以任意調整 num_controls (如 4, 5, 6, 8)，以及目標 theta
    engine = HsqDynamicQpeEngine(num_controls=15, target_theta=0.321, shots=2000)
    engine.run_dynamic_qpe()
