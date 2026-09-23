# ==============================================================================
# PURE HSQ GATE-LEVEL DRAPER PHASE ADDER (4-BIT QUANTUM ADDER)
# Fully Quantum Arithmetic | No Classical Python Addition
# ==============================================================================

import time
import numpy as np
import requests

SERVER_IP = "192.168.0.20"
BASE_PORT = 5011

class HsqDraperAdder:
    def __init__(self, num_bits: int = 4):
        self.num_bits = num_bits
        
        # A 暫存器 (Ports 5011 ~ 5014), B 暫存器 (Ports 5015 ~ 5018)
        self.reg_a_ports = [BASE_PORT + i for i in range(num_bits)]
        self.reg_b_ports = [BASE_PORT + num_bits + i for i in range(num_bits)]
        self.all_ports = self.reg_a_ports + self.reg_b_ports

    def _post(self, port: int, endpoint: str, payload: dict = None) -> dict:
        url = f"http://{SERVER_IP}:{port}/{endpoint}"
        return requests.post(url, json=payload or {}, timeout=5.0).json()

    def set_register_value(self, ports, val_int):
        """ 將數值轉換為二進位狀態注入 Qubits (|0> 或 |1>) """
        bit_str = f"{val_int:0{self.num_bits}b}" # 比如 3 -> '0011'
        for idx, bit in enumerate(bit_str):
            if bit == "1":
                self._post(ports[idx], "instruction", {"gate": "x"})

    def apply_qft(self, ports):
        """ 對暫存器施加正向 QFT (時域 -> 傅立葉相域) """
        n = len(ports)
        for i in range(n):
            self._post(ports[i], "instruction", {"gate": "h"})
            for j in range(i + 1, n):
                bus_key_j = f"draper_qft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })

    def apply_iqft(self, ports):
        """ 對暫存器施加逆向 IQFT (傅立葉相域 -> 時域) """
        n = len(ports)
        for i in range(n - 1, -1, -1):
            for j in range(n - 1, i, -1):
                bus_key_j = f"draper_iqft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = -np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })
            self._post(ports[i], "instruction", {"gate": "h"})

    def run_draper_addition(self, val_a: int = 3, val_b: int = 5):
        t0 = time.time()
        print("======================================================================")
        print(f"⚛️  [HSQ Draper Adder] 純量子邏輯閘 4-Bit 加法器")
        print(f"   ├─ 輸入 A 態 (|A>) : {val_a} (|{val_a:04b}>_2)")
        print(f"   ├─ 輸入 B 態 (|B>) : {val_b} (|{val_b:04b}>_2)")
        print("======================================================================\n")

        # Step 0: 全網真空重置
        for port in self.all_ports:
            self._post(port, "reset")

        # Step 1: 將狀態注入 A 與 B 暫存器
        self.set_register_value(self.reg_a_ports, val_a)
        self.set_register_value(self.reg_b_ports, val_b)

        # 導出 A 暫存器的狀態鎖定 Key (作為加法控制源)
        a_bus_keys = []
        for idx, port in enumerate(self.reg_a_ports):
            bus_key = f"draper_reg_a_q{idx}"
            self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key})
            a_bus_keys.append(bus_key)

        # Step 2: 對 B 暫存器執行 QFT 轉化至頻域
        print("🌀 Step 1: 對 B 暫存器施加 QFT，轉化至傅立葉頻域...")
        self.apply_qft(self.reg_b_ports)

        # Step 3: 傅立葉域相位相加 (Draper Phase Addition)
        # 用 A 暫存器的 Qubits 對 B 暫存器的 Qubits 施加受控 CPhase 旋轉
        print("⚡ Step 2: 執行純量子邏輯閘相位相加 (Controlled-Phase Rotations)...")
        for i in range(self.num_bits):
            # B 暫存器第 i 顆 Qubit
            port_b = self.reg_b_ports[i]
            for j in range(i, self.num_bits):
                # A 暫存器第 j 顆 Qubit
                bus_key_a = a_bus_keys[j]
                
                # 計算傅立葉相加角 θ = π / 2^(j - i)
                angle = np.pi / (2 ** (j - i))
                
                # 受控 CPhase 相位轉動 (完全透過 HSQ Tensor Bus 互鎖)
                self._post(port_b, "instruction", {
                    "gate": "cphase",
                    "delta_phi": angle,
                    "source_bus_key": bus_key_a
                })

        # Step 4: 對 B 暫存器執行 IQFT 轉回時域
        print("🌀 Step 3: 對 B 暫存器施加 IQFT，將加法結果解碼轉回時域...")
        self.apply_iqft(self.reg_b_ports)

        # Step 5: 讀取 B 暫存器最終的二進位態與幾何振幅
        result_bits = []
        for idx, port in enumerate(self.reg_b_ports):
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"final_b_{idx}"})
            b_r, b_i = res["state_b"][0], res["state_b"][1]
            prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
            bit_val = "1" if prob_1 > 0.5 else "0"
            result_bits.append(bit_val)

        bitstring = "".join(result_bits)
        result_int = int(bitstring, 2)
        t1 = time.time()

        print("\n======================================================================")
        print(f"✨ 運算後 B 暫存器二進位 : |{bitstring}>_2")
        print(f"✨ 解碼十進位結果        : {result_int}")
        print(f"🎯 純邏輯閘運算驗證     : {val_a} + {val_b} = {result_int} ({'成功' if result_int == val_a + val_b else '失敗'})")
        print(f"⏱️  純量子邏輯閘加法耗時 : {(t1 - t0)*1000:.2f} ms")
        print("======================================================================")

if __name__ == "__main__":
    adder = HsqDraperAdder(num_bits=4)
    # 測試 3 + 5
    adder.run_draper_addition(val_a=3, val_b=5)