# ==============================================================================
# PURE HSQ GATE-LEVEL MODULAR MULTIPLIER (LEVEL 3 - OPTION A FULLY CONTROLLED)
# Strict Controlled-Draper Modular Addition with Ancilla Uncomputing
# ==============================================================================

import time
import numpy as np
import requests

SERVER_IP = "192.168.0.20"
BASE_PORT = 5011

class HsqModularMultiplierOptionA:
    def __init__(self, num_bits: int = 4):
        self.num_bits = num_bits
        
        # Ports 分配:
        # Y 暫存器   : Ports 5011 ~ 5014
        # ACC 暫存器 : Ports 5015 ~ 5018
        # Ancilla    : Port  5019
        self.reg_y_ports = [BASE_PORT + i for i in range(num_bits)]
        self.reg_acc_ports = [BASE_PORT + num_bits + i for i in range(num_bits)]
        self.ancilla_port = BASE_PORT + 2 * num_bits
        
        self.all_ports = self.reg_y_ports + self.reg_acc_ports + [self.ancilla_port]

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
                bus_key_j = f"mult_qft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })

    def apply_iqft(self, ports):
        n = len(ports)
        for i in range(n - 1, -1, -1):
            for j in range(n - 1, i, -1):
                bus_key_j = f"mult_iqft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = -np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })
            self._post(ports[i], "instruction", {"gate": "h"})

    def controlled_draper_add_constant(self, const_val: int, target_ports, control_bus_key, sign=1.0):
        """ 受控 Draper 相位相加/相減：當 control_bus_key = |1> 時才執行 """
        bit_str = f"{const_val:0{self.num_bits}b}"
        for i in range(self.num_bits):
            port_target = target_ports[i]
            for j in range(i, self.num_bits):
                if bit_str[j] == "1":
                    angle = sign * np.pi / (2 ** (j - i))
                    self._post(port_target, "instruction", {
                        "gate": "cphase",
                        "delta_phi": angle,
                        "source_bus_key": control_bus_key
                    })

    def run_strictly_controlled_modular_addition(self, const_val: int, N: int, control_bus_key: str, stage_idx: int):
        """ 方案 A 完全體：嚴格受控模加法器 (若 control_bus_key=|0> 則 100% Bypass) """
        # 0. 重置 Ancilla 門狀態
        self._post(self.ancilla_port, "reset")

        # 1. ACC 進入傅立葉頻域
        self.apply_qft(self.reg_acc_ports)

        # 2. 受控 Draper 加法 (+K_j)，受 control_bus_key 嚴格控制
        self.controlled_draper_add_constant(const_val, self.reg_acc_ports, control_bus_key, sign=1.0)

        # 3. 受控 Draper 試探性減法 (-N)，同樣受 control_bus_key 嚴格控制！
        self.controlled_draper_add_constant(N, self.reg_acc_ports, control_bus_key, sign=-1.0)

        # 4. IQFT 轉回時域檢查借位/溢位
        self.apply_iqft(self.reg_acc_ports)

        # 5. 導出 ACC0 狀態，並使用 HSQ 的 CCNOT (Toffoli) 進行雙重控制 Ancilla 標記：
        #    只有當 Control_Y_j == |1> 且 ACC_0 == |1> 時，才翻轉 Ancilla Qubit！
        acc0_key = f"acc0_stg{stage_idx}"
        self._post(self.reg_acc_ports[0], "instruction", {"gate": "export_tensor_metric", "bus_key": acc0_key})

        # 呼叫三體高階 Toffoli 閘 (control_bus_key, acc0_key -> ancilla_port)
        double_control_keys = f"{control_bus_key},{acc0_key}"
        self._post(self.ancilla_port, "instruction", {
            "gate": "ccnot",
            "source_bus_key": double_control_keys
        })

        ancilla_key = f"ancilla_stg{stage_idx}"
        self._post(self.ancilla_port, "instruction", {"gate": "export_tensor_metric", "bus_key": ancilla_key})

        # 6. 受控加回 N (Restoration Step)：只有當 Ancilla == |1> 時加回 N
        self.apply_qft(self.reg_acc_ports)
        self.controlled_draper_add_constant(N, self.reg_acc_ports, ancilla_key, sign=1.0)
        self.apply_iqft(self.reg_acc_ports)

        # 7. Uncompute Ancilla：再次調用 CCNOT 恢復 Ancilla 狀態，完成狀態擦除
        self._post(self.ancilla_port, "instruction", {
            "gate": "ccnot",
            "source_bus_key": double_control_keys
        })

    def run_modular_multiplication(self, val_y: int = 3, a: int = 7, N: int = 11):
        t0 = time.time()
        expected_val = (a * val_y) % N
        print("======================================================================")
        print(f"⚛️  [HSQ Modular Multiplier] 純量子邏輯門 4-Bit 模乘法器 (方案 A 補完版)")
        print(f"   ├─ 輸入 Y 態 (|Y>) : {val_y} (|{val_y:04b}>_2)")
        print(f"   ├─ 乘數 a          : {a}")
        print(f"   ├─ 模數 N          : {N}")
        print(f"   └─ 理論計算預期    : ({a} × {val_y}) mod {N} = {expected_val}")
        print("======================================================================\n")

        # Step 0: 全網真空重置
        for port in self.all_ports:
            self._post(port, "reset")

        # Step 1: 注入輸入狀態 |Y> 到 Y 暫存器，ACC 保持 |0000>
        self.set_register_value(self.reg_y_ports, val_y)

        # Step 2: 正確位元權重對齊與嚴格受控累加
        print("⚡ Step 1: 執行嚴格受控模加法陣列 (Option A Fully-Controlled Additions)...")
        for j in range(self.num_bits):
            bit_weight = 2 ** (self.num_bits - 1 - j)
            k_j = (a * bit_weight) % N

            y_port = self.reg_y_ports[j]
            y_bus_key = f"mult_y_q{j}"
            self._post(y_port, "instruction", {"gate": "export_tensor_metric", "bus_key": y_bus_key})

            print(f"   ├─ 處理 Y[{j}] (權重 2^{self.num_bits - 1 - j} = {bit_weight}): 嚴格受控模加法 K_{j} = ({a} × {bit_weight}) mod {N} = {k_j}")
            if k_j > 0:
                self.run_strictly_controlled_modular_addition(const_val=k_j, N=N, control_bus_key=y_bus_key, stage_idx=j)

        # Step 3: 從 ACC 暫存器讀出最終量子模乘法結果
        print("\n🎯 Step 2: 從 ACC 暫存器讀取純量子模乘法最終態...")
        result_bits = []
        for idx, port in enumerate(self.reg_acc_ports):
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"final_acc_{idx}"})
            b_r, b_i = res["state_b"][0], res["state_b"][1]
            prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
            bit_val = "1" if prob_1 > 0.5 else "0"
            result_bits.append(bit_val)

        bitstring = "".join(result_bits)
        result_int = int(bitstring, 2)
        t1 = time.time()

        print("\n======================================================================")
        print(f"✨ ACC 暫存器最終二進位 : |{bitstring}>_2")
        print(f"✨ 解碼十進位結果        : {result_int}")
        print(f"🎯 純邏輯門模乘法驗證   : ({a} × {val_y}) mod {N} = {result_int} ({'成功' if result_int == expected_val else '失敗'})")
        print(f"⏱️  純量子模乘法耗時     : {(t1 - t0)*1000:.2f} ms")
        print("======================================================================")

if __name__ == "__main__":
    multiplier = HsqModularMultiplierOptionA(num_bits=4)
    multiplier.run_modular_multiplication(val_y=3, a=7, N=11)