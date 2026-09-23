# ==============================================================================
# PURE HSQ GATE-LEVEL MODULAR PHASE ADDER (4-BIT QUANTUM MODULAR ADDER)
# Implements: |B> -> |(B + A) mod N> without classical arithmetic
# ==============================================================================

import time
import numpy as np
import requests

SERVER_IP = "192.168.0.20"
BASE_PORT = 5011

class HsqModularAdder:
    def __init__(self, num_bits: int = 4):
        self.num_bits = num_bits  # 4 bits for number representation
        
        # A 暫存器 (Ports 5011~5014), B 暫存器 (Ports 5015~5018), Ancilla Qubit (Port 5019)
        self.reg_a_ports = [BASE_PORT + i for i in range(num_bits)]
        self.reg_b_ports = [BASE_PORT + num_bits + i for i in range(num_bits)]
        self.ancilla_port = BASE_PORT + 2 * num_bits
        
        self.all_ports = self.reg_a_ports + self.reg_b_ports + [self.ancilla_port]

    def _post(self, port: int, endpoint: str, payload: dict = None) -> dict:
        url = f"http://{SERVER_IP}:{port}/{endpoint}"
        return requests.post(url, json=payload or {}, timeout=5.0).json()

    def set_register_value(self, ports, val_int):
        """ 將數值轉換為二進位狀態注入 Qubits """
        bit_str = f"{val_int:0{self.num_bits}b}"
        for idx, bit in enumerate(bit_str):
            if bit == "1":
                self._post(ports[idx], "instruction", {"gate": "x"})

    def apply_qft(self, ports):
        n = len(ports)
        for i in range(n):
            self._post(ports[i], "instruction", {"gate": "h"})
            for j in range(i + 1, n):
                bus_key_j = f"mod_qft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })

    def apply_iqft(self, ports):
        n = len(ports)
        for i in range(n - 1, -1, -1):
            for j in range(n - 1, i, -1):
                bus_key_j = f"mod_iqft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = -np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })
            self._post(ports[i], "instruction", {"gate": "h"})

    def apply_draper_add_reg(self, reg_source_keys, target_ports, sign=1.0):
        """ 執行跨暫存器 Draper 相位相加/相減 """
        for i in range(self.num_bits):
            port_b = target_ports[i]
            for j in range(i, self.num_bits):
                bus_key_a = reg_source_keys[j]
                angle = sign * np.pi / (2 ** (j - i))
                self._post(port_b, "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_a
                })

    def apply_draper_add_constant(self, const_val: int, target_ports, sign=1.0):
        """ 在傅立葉域中對目標暫存器加/減常數 const_val """
        bit_str = f"{const_val:0{self.num_bits}b}"
        for i in range(self.num_bits):
            port_b = target_ports[i]
            for j in range(i, self.num_bits):
                if bit_str[j] == "1":
                    angle = sign * np.pi / (2 ** (j - i))
                    self._post(port_b, "instruction", {
                        "gate": "phase", "delta_phi": angle
                    })

    def run_modular_addition(self, val_a: int = 7, val_b: int = 6, N: int = 11):
        t0 = time.time()
        print("======================================================================")
        print(f"⚛️  [HSQ Modular Adder] 純量子邏輯閘 4-Bit 模加法器")
        print(f"   ├─ 輸入 A 態 (|A>) : {val_a} (|{val_a:04b}>_2)")
        print(f"   ├─ 輸入 B 態 (|B>) : {val_b} (|{val_b:04b}>_2)")
        print(f"   ├─ 模數 N          : {N}")
        print(f"   └─ 理論計算預期    : ({val_a} + {val_b}) mod {N} = {(val_a + val_b) % N}")
        print("======================================================================\n")

        # Step 0: 真空重置
        for port in self.all_ports:
            self._post(port, "reset")

        # Step 1: 狀態初始化
        self.set_register_value(self.reg_a_ports, val_a)
        self.set_register_value(self.reg_b_ports, val_b)

        # 導出 A 暫存器 Key
        a_bus_keys = []
        for idx, port in enumerate(self.reg_a_ports):
            bus_key = f"mod_reg_a_q{idx}"
            self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key})
            a_bus_keys.append(bus_key)

        # Step 2: B 暫存器轉至傅立葉頻域
        print("🌀 Step 1: 對 B 暫存器施加 QFT...")
        self.apply_qft(self.reg_b_ports)

        # Step 3: Draper 相位相加 (|B> -> |B + A>)
        print("⚡ Step 2: 執行 Draper 暫存器相位相加 |B> + |A>...")
        self.apply_draper_add_reg(a_bus_keys, self.reg_b_ports, sign=1.0)

        # Step 4: 試探性減去 N (|B + A> -> |B + A - N>)
        print(f"➖ Step 3: 試探性減去模數 N={N}...")
        self.apply_draper_add_constant(N, self.reg_b_ports, sign=-1.0)

        # Step 5: 轉回時域檢查借位/溢位 (Carry Check)
        print("🔍 Step 4: 轉回時域檢查溢位條件...")
        self.apply_iqft(self.reg_b_ports)

        # 導出最高位 B[0] 作為溢位控制源
        b0_key = "mod_b0_metric"
        self._post(self.reg_b_ports[0], "instruction", {"gate": "export_tensor_metric", "bus_key": b0_key})
        
        # 若最高位翻轉說明結果為負數 (借位)，觸發 CNOT 標記 Ancilla Qubit
        self._post(self.ancilla_port, "instruction", {
            "gate": "cnot",
            "source_bus_key": b0_key
        })

        # 導出 Ancilla Key 用於條件加回
        ancilla_key = "mod_ancilla_metric"
        self._post(self.ancilla_port, "instruction", {"gate": "export_tensor_metric", "bus_key": ancilla_key})

        # Step 6: 再次進入頻域，若溢位 (Ancilla=1) 則受控加回 N
        print("🌀 Step 5: 受控復原加回 N (Restoration Step)...")
        self.apply_qft(self.reg_b_ports)

        # 受控 Draper 加回 N (若 Ancilla=1，加回 N)
        bit_str_N = f"{N:0{self.num_bits}b}"
        for i in range(self.num_bits):
            port_b = self.reg_b_ports[i]
            for j in range(i, self.num_bits):
                if bit_str_N[j] == "1":
                    angle = np.pi / (2 ** (j - i))
                    self._post(port_b, "instruction", {
                        "gate": "cphase",
                        "delta_phi": angle,
                        "source_bus_key": ancilla_key
                    })

        # Step 7: 轉回時域，得到最終 (B + A) mod N 結果
        print("🌀 Step 6: 施加最終 IQFT 解碼模加法結果...")
        self.apply_iqft(self.reg_b_ports)

        # Step 8: 讀取最終 B 暫存器狀態
        result_bits = []
        for idx, port in enumerate(self.reg_b_ports):
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"final_mod_b_{idx}"})
            b_r, b_i = res["state_b"][0], res["state_b"][1]
            prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
            bit_val = "1" if prob_1 > 0.5 else "0"
            result_bits.append(bit_val)

        bitstring = "".join(result_bits)
        result_int = int(bitstring, 2)
        expected_val = (val_a + val_b) % N
        t1 = time.time()

        print("\n======================================================================")
        print(f"✨ 運算後 B 暫存器二進位 : |{bitstring}>_2")
        print(f"✨ 解碼十進位結果        : {result_int}")
        print(f"🎯 純邏輯閘模加法驗證   : ({val_a} + {val_b}) mod {N} = {result_int} ({'成功' if result_int == expected_val else '失敗'})")
        print(f"⏱️  純量子模加法耗時     : {(t1 - t0)*1000:.2f} ms")
        print("======================================================================")

if __name__ == "__main__":
    mod_adder = HsqModularAdder(num_bits=4)
    # 測試 (7 + 6) mod 11 = 2
    mod_adder.run_modular_addition(val_a=7, val_b=6, N=11)