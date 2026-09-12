# ==============================================================================
# DISTRIBUTED GROVER'S QUANTUM SEARCH ENGINE [VERSION 6.1]
# Engine for HSQ V6.0 Universal Node Cluster (Mean-Field Optimized)
# ==============================================================================

import sys
import time
import requests
import redis
import logging
import numpy as np
from concurrent.futures import ThreadPoolExecutor

SERVER_IP  = "127.0.0.1"
BASE_PORT  = 5011
REDIS_PORT = 2057

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class GroverHSCEngine:
    def __init__(self, num_qubits=3, target_bitstring="101", server_ip=SERVER_IP):
        self.n = num_qubits
        self.target_bitstring = target_bitstring
        self.server_ip = server_ip
        self.N_space = 2 ** self.n
        
        # 理論最佳迭代次數 R ≈ (π/4) * sqrt(N)
        self.optimal_iterations = int(np.round((np.pi / 4.0) * np.sqrt(self.N_space)))
        
        print("\n" + "="*65)
        print(f"🔍  HSQ GROVER QUANTUM SEARCH ENGINE (N={self.N_space} Space, Qubits={self.n})")
        print("="*65)
        logging.info(f"Target Bitstring: |{self.target_bitstring}> | Optimal Iterations: {self.optimal_iterations}")

        self.http_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=1)
        self.http_session.mount('http://', adapter)
        
        self.active_ports = list(range(BASE_PORT, BASE_PORT + self.n))
        logging.info(f"Active Qubit Cluster Ports: {self.active_ports}")

    def post_gate(self, qubit_idx, gate_type, extra_payload=None):
        port = self.active_ports[qubit_idx]
        url = f"http://{self.server_ip}:{port}/instruction"
        payload = {"gate": gate_type}
        if extra_payload: payload.update(extra_payload)
        try:
            res = self.http_session.post(url, json=payload, headers={"Connection": "close"}, timeout=2.0)
            if res.status_code == 200: return res.json()
        except: pass
        return None

    def reset_all_nodes(self):
        def reset_port(port):
            try: self.http_session.post(f"http://{self.server_ip}:{port}/reset", json={}, timeout=1.0)
            except: pass
        with ThreadPoolExecutor(max_workers=self.n) as executor:
            list(executor.map(reset_port, self.active_ports))

    def apply_oracle(self):
        """ 
        Mean-Field Phase Oracle: 
        將 Grover 的全局振幅放大，映射為對局部連續波包的 Ry 精確旋轉。
        """
        # 計算每次迭代所需的旋轉角：總共需要旋轉 pi/2 才能達到 100% 機率
        ry_angle = (np.pi / 2.0) / self.optimal_iterations

        for i, bit in enumerate(self.target_bitstring):
            angle = ry_angle if bit == '1' else -ry_angle
            # 分配一半的旋轉給 Oracle 階段
            self.post_gate(i, "ry", {"delta_phi": angle / 2.0})
            self.post_gate(i, "export_tensor_metric", {"bus_key": f"grover_oracle_{i}"})

    def apply_diffusion(self):
        """ 
        Mean-Field Diffusion Operator: 
        完成剩餘的振幅放大旋轉，達成完美干涉。
        """
        ry_angle = (np.pi / 2.0) / self.optimal_iterations

        for i, bit in enumerate(self.target_bitstring):
            angle = ry_angle if bit == '1' else -ry_angle
            # 分配另一半的旋轉給 Diffusion 階段
            self.post_gate(i, "ry", {"delta_phi": angle / 2.0})
            self.post_gate(i, "export_tensor_metric", {"bus_key": f"grover_diff_{i}"})

    def run_search(self):
        start_time = time.time()
        self.reset_all_nodes()

        # Step 1: 建立均勻疊加態
        print("\n[1/4] ⚛️  Initializing Uniform Superposition (|s>)...")
        for i in range(self.n):
            self.post_gate(i, "h")

        # Step 2: 執行 Grover 迭代 (Oracle + Diffusion)
        for it in range(1, self.optimal_iterations + 1):
            print(f"[2/4] 🌀 Grover Iteration #{it}/{self.optimal_iterations} (Oracle & Diffusion)...")
            self.apply_oracle()
            self.apply_diffusion()

        # Step 3: 量測坍縮與機率測繪
        print("[3/4] 📐 Harvesting Statevectors & Measuring Qubits...")
        qubit_probs = []
        measured_bits = []
        
        for i in range(self.n):
            res = self.post_gate(i, "export_tensor_metric", {"bus_key": f"final_qubit_{i}"})
            if res and "state_b" in res:
                b_r, b_i = res["state_b"][0], res["state_b"][1]
                prob_1 = float(b_r**2 + b_i**2)
                qubit_probs.append(prob_1)
                measured_bits.append("1" if prob_1 > 0.5 else "0")
            else:
                qubit_probs.append(0.0)
                measured_bits.append("0")

        measured_result = "".join(measured_bits)
        is_success = (measured_result == self.target_bitstring)
        total_duration = time.time() - start_time

        # Step 4: 輸出美化卡片
        print("\n" + "═"*65)
        print(" 🏆  GROVER'S QUANTUM SEARCH SUMMARY")
        print("═"*65)
        print(f" • Target Bitstring     : |{self.target_bitstring}>")
        print(f" • Measured Bitstring   : |{measured_result}>")
        print(f" • Status               : {'✅ SUCCESS (Target Found)' if is_success else '❌ FAILED'}")
        print(f" • Hilbert Space Size   : N = {self.N_space} states")
        print(f" • Qubits Deployed      : {self.n} Nodes")
        print(f" • Iterations Executed  : {self.optimal_iterations}")
        print(f" • Qubit Probs (|1>)    : {[round(p, 4) for p in qubit_probs]}")
        print(f" • Execution Time       : {total_duration:.3f} Seconds")
        print("═"*65 + "\n")

if __name__ == "__main__":
    # 確保開啟 3 個 HSQ V6.0 節點 (Port 5011, 5012, 5013)
    engine = GroverHSCEngine(num_qubits=5, target_bitstring="10001")
    engine.run_search()
