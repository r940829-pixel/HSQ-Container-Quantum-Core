# ==============================================================================
# HOLOGRAPHIC QUANTUM PHASE ESTIMATION (QPE) ENGINE [ANALYTIC INTERFEROMETRY EDITION]
# Dynamic Control Nodes Generation | Zero-Noise Native Geometric Metric Projection
# ==============================================================================

import time
import numpy as np
import requests
from typing import List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SERVER_IP = "127.0.0.1"
BASE_PORT = 5011

class HsqAnalyticQpeEngine:
    def __init__(self, num_controls: int = 15, target_theta: float = 0.321):
        self.num_controls = num_controls
        self.theta = target_theta
        
        # 動態分配 Ports：Q0 ~ Q(n-1) 為 Control，最後一顆為 Target
        self.control_ports = [BASE_PORT + i for i in range(self.num_controls)]
        self.target_port = BASE_PORT + self.num_controls
        self.all_ports = self.control_ports + [self.target_port]

        # 建立高併發 HTTP 連線池
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

    def run_analytic_qpe(self):
        t0 = time.time()
        print("======================================================================")
        print(f"⚛️  [Analytic QPE] 啟動 HSQ 原生幾何干涉量子相位估計 (純 Metric 解析)")
        print(f"  ├─ 目標相角 (θ)  : {self.theta}")
        print(f"  ├─ Control 節點  : {self.num_controls} 顆 (Ports: {self.control_ports[0]}~{self.control_ports[-1]})")
        print(f"  ├─ Target  節點  : 1 顆 (Port: {self.target_port})")
        print(f"  └─ 理論解析度    : 1 / {2**self.num_controls} = {1/(2**self.num_controls):.10f}")
        print("======================================================================\n")

        # Step 0: 系統 Vacuum 重置
        for port in self.all_ports:
            self._post(port, "reset")

        # Step 1: 狀態準備 (Target 初始化為 |1> 態, Control 初始化為 H 疊加態)
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

        # Step 3: 動態 Inverse QFT (IQFT) 拓樸幹涉
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
            # 拓樸相位軸向干涉旋轉 (H 門干涉)
            self._post(port_i, "instruction", {"gate": "h"})
        print("✅ 逆量子傅立葉變換 (IQFT) 拓樸幾何干涉完成。\n")

        # ======================================================================
        # Step 4: 幾何干涉投影解析 (無 Shots 統計, 100% 幾何場直讀)
        # ======================================================================
        probabilities = []
        analytic_bits = []

        for i, port in enumerate(self.control_ports):
            # 廣播並導出最終 Spinor Metric
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"dyn_final_q{i}"})
            b_r, b_i = res["state_b"][0], res["state_b"][1]
            
            # |b|^2 幾何干涉機率
            prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
            probabilities.append(prob_1)

            # 幾何干涉投影判定: 機率 > 0.5 判定為 1, 否則為 0
            bit_val = "1" if prob_1 > 0.5 else "0"
            analytic_bits.append(bit_val)

        # 二進位字串 (Q0 順序對齊 -> 小數第一位為 MSB, 最後一位為 LSB)
        bitstring = "".join(analytic_bits)

        # 導出十進位相位數值 (純幾何解析)
        decimal_val = 0.0
        for idx, bit in enumerate(analytic_bits):
            if bit == "1":
                decimal_val += 1.0 / (2 ** (idx + 1))

        t1 = time.time()

        # 輸出微觀物理幾何干涉振幅
        prob_str = " | ".join([f"Q{i}:{p:.4f}" for i, p in enumerate(probabilities)])
        print(f"📊 [幾何干涉 Spinor 振幅] {prob_str}")

        print("\n======================================================================")
        print(f"✨ 目標真實相角 (θ)   : {self.theta}")
        print(f"✨ 幾何干涉導出二進位 : 0.{bitstring} (二進位)")
        print(f"✨ 推導幾何相位數值   : {decimal_val:.10f}")
        print(f"✨ 絕對誤差 (Error)   : {abs(self.theta - decimal_val):.10f}")
        print(f"⏱️  場域解算耗時       : {(t1 - t0)*1000:.2f} ms")
        print("======================================================================")

if __name__ == "__main__":
    # 測試 15 顆 Control Nodes (可任意改為 4, 8, 15, 30, 61 顆，無需擔心 Shots 稀釋)
    engine = HsqAnalyticQpeEngine(num_controls=15, target_theta=0.321)
    engine.run_analytic_qpe()
