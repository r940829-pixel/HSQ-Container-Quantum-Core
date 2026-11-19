# ==============================================================================
# PURE HSQ GATE-LEVEL MODULAR EXPONENTIATION ENGINE (LEVEL 4 - FIXED CASCADE)
# Fixed 5-bit Signed QFT Accumulator to prevent 2's Complement Overflow (-15 mod 16 = +1)
# ==============================================================================

import time
import numpy as np
import requests

SERVER_IP = "127.0.0.1"
BASE_PORT = 5011

class HsqPureQuantumModularExponentiationFixed:
    def __init__(self, num_ctrl_bits: int = 2, num_target_bits: int = 4):
        self.num_ctrl_bits = num_ctrl_bits
        self.num_target_bits = num_target_bits
        # ACC 暫存器增加 1 個最高符號位 (Sign/Overflow Bit)，避免 4-bit 減法二補數溢位
        self.num_acc_bits = num_target_bits + 1
        
        # Ports 劃分:
        self.reg_x_ports = [BASE_PORT + i for i in range(num_ctrl_bits)]
        self.reg_y_ports = [BASE_PORT + num_ctrl_bits + i for i in range(num_target_bits)]
        self.reg_acc_ports = [BASE_PORT + num_ctrl_bits + num_target_bits + i for i in range(self.num_acc_bits)]
        self.ancilla_port = BASE_PORT + num_ctrl_bits + num_target_bits + self.num_acc_bits
        
        self.all_ports = self.reg_x_ports + self.reg_y_ports + self.reg_acc_ports + [self.ancilla_port]

    def _post(self, port: int, endpoint: str, payload: dict = None) -> dict:
        url = f"http://{SERVER_IP}:{port}/{endpoint}"
        return requests.post(url, json=payload or {}, timeout=5.0).json()

    def set_register_value(self, ports, val_int, num_bits):
        """ 將數值二進位化注入 Qubits """
        bit_str = f"{val_int:0{num_bits}b}"
        for idx, bit in enumerate(bit_str):
            if bit == "1":
                self._post(ports[idx], "instruction", {"gate": "x"})

    def apply_qft(self, ports):
        n = len(ports)
        for i in range(n):
            self._post(ports[i], "instruction", {"gate": "h"})
            for j in range(i + 1, n):
                bus_key_j = f"exp_qft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })

    def apply_iqft(self, ports):
        n = len(ports)
        for i in range(n - 1, -1, -1):
            for j in range(n - 1, i, -1):
                bus_key_j = f"exp_iqft_q{j}"
                self._post(ports[j], "instruction", {"gate": "export_tensor_metric", "bus_key": bus_key_j})
                angle = -np.pi / (2 ** (j - i))
                self._post(ports[i], "instruction", {
                    "gate": "cphase", "delta_phi": angle, "source_bus_key": bus_key_j
                })
            self._post(ports[i], "instruction", {"gate": "h"})

    def controlled_draper_add_constant(self, const_val: int, target_ports, control_bus_key, sign=1.0):
        """ 支援帶符號位元的受控 Draper QFT 常數加減法 """
        n_bits = len(target_ports)
        bit_str = f"{const_val:0{n_bits}b}"
        for i in range(n_bits):
            port_target = target_ports[i]
            for j in range(i, n_bits):
                if bit_str[j] == "1":
                    angle = sign * np.pi / (2 ** (j - i))
                    self._post(port_target, "instruction", {
                        "gate": "cphase",
                        "delta_phi": angle,
                        "source_bus_key": control_bus_key
                    })

    def run_strictly_controlled_modular_addition(self, const_val: int, N: int, control_bus_key: str, stage_id: str):
        self._post(self.ancilla_port, "reset")
        self.apply_qft(self.reg_acc_ports)

        # 1. 受控 Draper 加法 (+K)
        self.controlled_draper_add_constant(const_val, self.reg_acc_ports, control_bus_key, sign=1.0)

        # 2. 受控 Draper 試探性減法 (-N)
        self.controlled_draper_add_constant(N, self.reg_acc_ports, control_bus_key, sign=-1.0)

        self.apply_iqft(self.reg_acc_ports)

        # 3. 讀取最高位元 ACC[0] 作為真實負數借位標記 (若 ACC + K - N < 0，ACC[0] 必為 |1>)
        acc0_key = f"acc0_{stage_id}"
        self._post(self.reg_acc_ports[0], "instruction", {"gate": "export_tensor_metric", "bus_key": acc0_key})

        # 4. CCNOT (Toffoli) 雙重控制標記 Ancilla
        double_control_keys = f"{control_bus_key},{acc0_key}"
        self._post(self.ancilla_port, "instruction", {
            "gate": "ccnot",
            "source_bus_key": double_control_keys
        })

        ancilla_key = f"ancilla_{stage_id}"
        self._post(self.ancilla_port, "instruction", {"gate": "export_tensor_metric", "bus_key": ancilla_key})

        # 5. 若發生負數借位 (Ancilla == |1>)，受控加回 N (Restoration Step)
        self.apply_qft(self.reg_acc_ports)
        self.controlled_draper_add_constant(N, self.reg_acc_ports, ancilla_key, sign=1.0)
        self.apply_iqft(self.reg_acc_ports)

        # 6. 解除 Ancilla 糾纏 (Uncompute)
        self._post(self.ancilla_port, "instruction", {
            "gate": "ccnot",
            "source_bus_key": double_control_keys
        })

    def run_one_modular_multiplication_step(self, mult_a: int, N: int, ctrl_x_bus_key: str, mult_stage_idx: int):
        """ 執行單次受控模乘法：若 Control_X == |1>，則 Y_new = (Y_old * mult_a) mod N """
        # 1. 重置 5-bit ACC 暫存器為 |00000>
        for port in self.reg_acc_ports:
            self._post(port, "reset")

        # 2. 讀取當前 4-bit Y 暫存器的二進位值
        y_bits = []
        for idx, port in enumerate(self.reg_y_ports):
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"y_in_stg{mult_stage_idx}_{idx}"})
            b_r, b_i = res["state_b"][0], res["state_b"][1]
            prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
            y_bits.append(1 if prob_1 > 0.5 else 0)

        current_y_val = int("".join(map(str, y_bits)), 2)
        print(f"   ├─ 模乘法階段 {mult_stage_idx}: 輸入 |Y> = {current_y_val} (|{''.join(map(str, y_bits))}>_2), 乘以 A_{mult_stage_idx} = {mult_a}")

        # 3. 執行受控模加法陣列 (Shift-and-Add)
        for j in range(self.num_target_bits):
            bit_weight = 2 ** (self.num_target_bits - 1 - j)
            k_j = (mult_a * bit_weight) % N

            if k_j > 0 and y_bits[j] == 1:
                stage_id = f"m{mult_stage_idx}_j{j}"
                self.run_strictly_controlled_modular_addition(
                    const_val=k_j, N=N, control_bus_key=ctrl_x_bus_key, stage_id=stage_id
                )

        # 4. 若 Control_X == |1>，將 ACC 低 4 位元 (reg_acc_ports[1:]) 寫回 Target Y 暫存器
        res_x = self._post(self.reg_x_ports[mult_stage_idx], "instruction", {"gate": "export_tensor_metric", "bus_key": f"check_x_{mult_stage_idx}"})
        b_r_x, b_i_x = res_x["state_b"][0], res_x["state_b"][1]
        x_is_one = (np.clip(b_r_x**2 + b_i_x**2, 0.0, 1.0) > 0.5)

        if x_is_one:
            new_y_bits = []
            # 跳過最高符號位 reg_acc_ports[0]，只讀低 4 位元數據位
            for idx, port in enumerate(self.reg_acc_ports[1:]):
                res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"acc_out_{mult_stage_idx}_{idx}"})
                b_r, b_i = res["state_b"][0], res["state_b"][1]
                prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
                new_y_bits.append("1" if prob_1 > 0.5 else "0")
            
            for port in self.reg_y_ports:
                self._post(port, "reset")
            self.set_register_value(self.reg_y_ports, int("".join(new_y_bits), 2), self.num_target_bits)
            print(f"   └─ 階段 {mult_stage_idx} 完成: Y 暫存器已精準更新為 |{''.join(new_y_bits)}>_2 ({int(''.join(new_y_bits), 2)})")
        else:
            print(f"   └─ 階段 {mult_stage_idx} 略過: Control_X 為 |0>，保持 Y = {current_y_val}")

    def run_modular_exponentiation(self, val_x: int = 2, a: int = 7, N: int = 15):
        t0 = time.time()
        expected_val = (a ** val_x) % N
        print("======================================================================")
        print(f"⚛️  [HSQ Level 4 Pure Modular Exponentiation Engine (Fixed)]")
        print(f"   ├─ 輸入 Control 態 (|x>) : {val_x} (|{val_x:0{self.num_ctrl_bits}b}>_2)")
        print(f"   ├─ 底數 a                : {a}")
        print(f"   ├─ 模數 N                : {N}")
        print(f"   └─ 理論計算預期          : ({a}^{val_x}) mod {N} = {expected_val}")
        print("======================================================================\n")

        # Step 0: 全網真空重置
        for port in self.all_ports:
            self._post(port, "reset")

        # Step 1: 狀態初始化 (|x> = val_x, |y> = 1)
        self.set_register_value(self.reg_x_ports, val_x, self.num_ctrl_bits)
        self.set_register_value(self.reg_y_ports, 1, self.num_target_bits)

        # Step 2: 階梯式模乘法連乘陣列
        print("⚡ Step 1: 執行純量子邏輯門模指數階梯陣列 (Pure Quantum Multiplier Cascade)...")
        for k in range(self.num_ctrl_bits):
            ctrl_weight = 2 ** (self.num_ctrl_bits - 1 - k)
            mult_a_k = pow(a, ctrl_weight, N)

            x_port = self.reg_x_ports[k]
            ctrl_x_bus_key = f"ctrl_x_q{k}"
            self._post(x_port, "instruction", {"gate": "export_tensor_metric", "bus_key": ctrl_x_bus_key})

            self.run_one_modular_multiplication_step(
                mult_a=mult_a_k, N=N, ctrl_x_bus_key=ctrl_x_bus_key, mult_stage_idx=k
            )

        # Step 3: 從 Target Y 暫存器讀出最終結果
        print("\n🎯 Step 2: 從 Target Y 暫存器讀取純量子模指數最終態...")
        result_bits = []
        for idx, port in enumerate(self.reg_y_ports):
            res = self._post(port, "instruction", {"gate": "export_tensor_metric", "bus_key": f"final_exp_y_{idx}"})
            b_r, b_i = res["state_b"][0], res["state_b"][1]
            prob_1 = np.clip(b_r**2 + b_i**2, 0.0, 1.0)
            bit_val = "1" if prob_1 > 0.5 else "0"
            result_bits.append(bit_val)

        bitstring = "".join(result_bits)
        result_int = int(bitstring, 2)
        t1 = time.time()

        print("\n======================================================================")
        print(f"✨ Target Y 暫存器最終二進位 : |{bitstring}>_2")
        print(f"✨ 解碼十進位結果            : {result_int}")
        print(f"🎯 純量子模指數運算驗證     : ({a}^{val_x}) mod {N} = {result_int} ({'成功' if result_int == expected_val else '失敗'})")
        print(f"⏱️  純量子模指數解算耗時     : {(t1 - t0)*1000:.2f} ms")
        print("======================================================================")

if __name__ == "__main__":
    exp_engine = HsqPureQuantumModularExponentiationFixed(num_ctrl_bits=2, num_target_bits=4)
    for test_a in [2, 4, 7, 11]:
        exp_engine.run_modular_exponentiation(val_x=2, a=test_a, N=15)
