import requests
import numpy as np

BASE_IP = "192.168.0.20"

# 🌐 定義 L=3 (12 顆 HSQ 節點) 分散式通道映射
NODES = {
    "L_C1": [f"http://{BASE_IP}:5011", f"http://{BASE_IP}:5012", f"http://{BASE_IP}:5013"],
    "L_C2": [f"http://{BASE_IP}:5014", f"http://{BASE_IP}:5015", f"http://{BASE_IP}:5016"],
    "L_A" : [f"http://{BASE_IP}:5017", f"http://{BASE_IP}:5018", f"http://{BASE_IP}:5019"],
    "L_b" : [f"http://{BASE_IP}:5020", f"http://{BASE_IP}:5021", f"http://{BASE_IP}:5022"]
}

# 🔐 設定 L=3 (3-bit) 的 LWE 代數數據
A_MATRIX  = [1.0, 0.0, 0.0]
B_VECTOR  = [1.0, 1.0, 1.0]
C1_CIPHER = [1.0, 1.0, 1.0]
C2_CIPHER = [0.0, 0.0, 0.0]

def reset_all_hsq_cluster():
    for group_name, url_list in NODES.items():
        for url in url_list:
            requests.post(f"{url}/reset", timeout=2.0)

def apply_gate(node_url, gate_name, delta_phi=0.0, source_bus_key=None):
    payload = {"gate": gate_name, "delta_phi": delta_phi, "source_bus_key": source_bus_key}
    return requests.post(f"{node_url}/instruction", json=payload, timeout=5.0).json()

def export_metric(node_url, bus_key):
    return requests.post(f"{node_url}/instruction", json={"gate": "export_tensor_metric", "bus_key": bus_key}, timeout=5.0).json()

def run_l3_fixed_lwe_experiment(noise_level=0.05):
    print(f"🚀 啟動【L=3 | N=8 | 12 顆 HSQ 容器】修復版 LWE 密文解密測試...")
    reset_all_hsq_cluster()

    # 1. 數據初始化：將 LWE 密文與公鑰進行 X 門位元翻轉
    print("📥 進行 12 通道 LWE 相位初始化 (X 門 + H 門)...")
    for i in range(3):
        if C1_CIPHER[i] == 1.0: apply_gate(NODES["L_C1"][i], "x")
        if C2_CIPHER[i] == 1.0: apply_gate(NODES["L_C2"][i], "x")
        if A_MATRIX[i]  == 1.0: apply_gate(NODES["L_A"][i],  "x")
        if B_VECTOR[i]  == 1.0: apply_gate(NODES["L_b"][i],  "x")

    # 2. 進入均勻疊加態
    for group in NODES.values():
        for url in group:
            apply_gate(url, "h")

    # 3. L_C1 暫存器觸發微觀張量編織，導出獨立的 B2 匯流排 (q0, q1, q2)
    b2_keys = []
    for idx, url in enumerate(NODES["L_C1"]):
        key = f"hsq:bus:B2:q{idx}"
        b2_keys.append(key)
        export_metric(url, key)

    # 4. 執行 12 通道獨立連鎖消相干
    print("🔄 執行 12 通道對應消相干抵銷與相位相銷...")
    for i in range(3):
        apply_gate(NODES["L_A"][i], "cnot_interlock", source_bus_key=b2_keys[i])
        apply_gate(NODES["L_b"][i], "cnot_interlock", source_bus_key=b2_keys[i])

    # 5. 🛠️ 修正點：對 L_C2 進行「Bit-wise 一對一獨立通道對齊鎖定」
    for i in range(3):
        url = NODES["L_C2"][i]
        single_bus_key = b2_keys[i]  # 精確鎖定對應通道的 Bus Key
        
        apply_gate(url, "h")
        apply_gate(url, "cz", source_bus_key=single_bus_key)
        apply_gate(url, "cnot_interlock", source_bus_key=single_bus_key)
        apply_gate(url, "h")

    # 7. 讀取最終解密結果
    extracted_mu = []
    print("\n--------------------------------------------------------")
    print(f"🎯 L=3 (12 通道修復版) LWE 解密測量結果 [L_C2 暫存器]:")

    for i, url in enumerate(NODES["L_C2"]):
        res = export_metric(url, f"hsq:bus:l3_result_q{i}")
        b_real, b_imag = res["state_b"][0], res["state_b"][1]
        prob_1 = b_real**2 + b_imag**2

        bit_val = 1 if prob_1 > 0.5 else 0
        extracted_mu.append(bit_val)
        print(f"   明文位元 {i} (Qubit {i}) |1> 機率 P(|1>): {prob_1:.6f} -> 解出明文: {bit_val}")

    print(f"\n   🔓 HSQ (12 顆容器) 成功還原的明文內容 mu = {extracted_mu}")
    print("--------------------------------------------------------")
    return extracted_mu

if __name__ == "__main__":
    run_l3_fixed_lwe_experiment(noise_level=0.05)