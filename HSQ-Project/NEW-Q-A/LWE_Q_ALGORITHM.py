import sys
import time
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor

BASE_IP = "127.0.0.1"
START_PORT = 5011

class BlindLWEBreakerFixed:
    def __init__(self, server_ip=BASE_IP, start_port=START_PORT):
        self.server_ip = server_ip
        self.start_port = start_port
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=1)
        self.session.mount("http://", adapter)

    def _post_gate(self, port, gate, delta_phi=0.0, source_bus_key=None, bus_key=None):
        url = f"http://{self.server_ip}:{port}/instruction"
        payload = {"gate": gate, "delta_phi": delta_phi, "source_bus_key": source_bus_key, "bus_key": bus_key}
        try:
            res = self.session.post(url, json=payload, headers={"Connection": "close"}, timeout=3.0)
            if res.status_code == 200:
                return res.json()
        except:
            pass
        return None

    def reset_cluster(self, ports):
        def _reset(p):
            try:
                self.session.post(f"http://{self.server_ip}:{p}/reset", timeout=1.5)
            except:
                pass
        with ThreadPoolExecutor(max_workers=len(ports)) as ex:
            list(ex.map(_reset, ports))

    def hex_to_bits(self, hex_str: str) -> list:
        hex_clean = hex_str.replace("0x", "").replace(" ", "")
        num_bits = len(hex_clean) * 4
        val = int(hex_clean, 16)
        bit_str = f"{val:0{num_bits}b}"
        return [int(b) for b in bit_str]

    def run_blind_attack(self, c1_hex: str, c2_hex: str):
        c1_bits = self.hex_to_bits(c1_hex)
        c2_bits = self.hex_to_bits(c2_hex)
        n_bits = len(c1_bits)
        assert len(c1_bits) == len(c2_bits), "C1 與 C2 長度必須一致！"

        # 動態分配連接埠
        c1_ports = [self.start_port + i for i in range(n_bits)]
        c2_ports = [self.start_port + n_bits + i for i in range(n_bits)]
        all_ports = c1_ports + c2_ports

        print("\n" + "="*75)
        print("🚩 【紅方視角】HSQ 分散式 LWE 盲破譯演習（修復版：消除 CZ 單向覆蓋）")
        print("="*75)
        print(f"📥 截獲公開密文: C1 = {c1_hex} | C2 = {c2_hex}")
        print(f"⚙️ 密文長度: {n_bits} Bits | 自動動態調度 HSQ 節點: {len(all_ports)} 顆")
        print(f"   • L_C1 暫存器通道: Port {c1_ports[0]} ~ {c1_ports[-1]}")
        print(f"   • L_C2 暫存器通道: Port {c2_ports[0]} ~ {c2_ports[-1]}")
        print("---------------------------------------------------------------------------")

        # 1. 叢集重設
        self.reset_cluster(all_ports)

        # 2. 密文狀態寫入（維持計算基底 |c1> 與 |c2>，消除無效 H 門引發的覆蓋）
        def _init_c1(idx):
            if c1_bits[idx] == 1:
                self._post_gate(c1_ports[idx], "x")

        def _init_c2(idx):
            if c2_bits[idx] == 1:
                self._post_gate(c2_ports[idx], "x")

        with ThreadPoolExecutor(max_workers=n_bits) as ex:
            list(ex.map(_init_c1, range(n_bits)))
            list(ex.map(_init_c2, range(n_bits)))

        # 3. L_C1 導出匯流排狀態
        c1_bus_keys = [f"hsq:bus:red_c1:q{i}" for i in range(n_bits)]
        def _export_c1(idx):
            self._post_gate(c1_ports[idx], "export_tensor_metric", bus_key=c1_bus_keys[idx])
        with ThreadPoolExecutor(max_workers=n_bits) as ex:
            list(ex.map(_export_c1, range(n_bits)))

        all_c1_keys_str = ",".join(c1_bus_keys)

        # 4. 🛠️ L_C2 執行對稱相消（移除 cz 投影覆蓋，保留兩組密文特徵）
        def _interlock_c2(idx):
            port = c2_ports[idx]
            single_key = c1_bus_keys[idx]
            
            # (a) 以 CNOT Interlock 進行對稱差分相消 (保留 C2 同時吸收 C1)
            self._post_gate(port, "cnot_interlock", source_bus_key=single_key)
            
            # (b) 全域多體聚合相位鎖定（平均場連續校準）
            self._post_gate(port, "csync_phase", source_bus_key=all_c1_keys_str)

        with ThreadPoolExecutor(max_workers=n_bits) as ex:
            list(ex.map(_interlock_c2, range(n_bits)))

        # 5. 測量 L_C2 輸出
        extracted_bits = [0] * n_bits
        probs = [0.0] * n_bits

        def _measure(idx):
            res = self._post_gate(c2_ports[idx], "export_tensor_metric", bus_key=f"hsq:bus:red_res_q{idx}")
            if res and "state_b" in res:
                b_r, b_i = res["state_b"][0], res["state_b"][1]
                p1 = float(b_r**2 + b_i**2)
                probs[idx] = p1
                extracted_bits[idx] = 1 if p1 > 0.5 else 0

        with ThreadPoolExecutor(max_workers=n_bits) as ex:
            list(ex.map(_measure, range(n_bits)))

        # 6. 結果解碼與展示
        bitstring = "".join(str(b) for b in extracted_bits)
        hex_sig = f"0x{int(bitstring, 2):02X}"
        ascii_char = chr(int(bitstring, 2)) if 32 <= int(bitstring, 2) <= 126 else "[不可見字元/數值標籤]"

        print("🎯 【紅方盲破譯推演完成 - 提交結果】")
        print(f" • 輸出 Bitstring (二進位) : |{bitstring}>")
        print(f" • 解碼 Hex 特徵標籤      : {hex_sig}")
        print(f" • 字符標籤推演           : {ascii_char}")
        print(f" • 各通道 P(|1>) 機率分佈 : {[round(p, 4) for p in probs]}")
        print(f" • 平均波場相干度         : {np.mean(probs):.4f}")
        print("="*75 + "\n")

        return bitstring, hex_sig, probs

if __name__ == "__main__":
    breaker = BlindLWEBreakerFixed(server_ip=BASE_IP, start_port=START_PORT)
    # 執行原題目驗證 (C1 = 0x5A, C2 = 0x19)
    breaker.run_blind_attack(c1_hex="0x5A", c2_hex="0x19")
