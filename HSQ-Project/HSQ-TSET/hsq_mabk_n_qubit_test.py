import math
import itertools
import requests
import numpy as np

# 🌐 設定 N 顆 HSQ 容器節點的 Base URL (例如 N=4, 5, 6...)
BASE_IP = "127.0.0.1"
START_PORT = 5011

def get_node_urls(n_qubits: int):
    return [f"http://{BASE_IP}:{START_PORT + i}" for i in range(n_qubits)]

def reset_cluster(nodes):
    for url in nodes:
        requests.post(f"{url}/reset", timeout=2.0)

def apply_gate(node_url, gate_name, delta_phi=0.0, source_bus_key=None):
    payload = {"gate": gate_name, "delta_phi": delta_phi, "source_bus_key": source_bus_key}
    return requests.post(f"{node_url}/instruction", json=payload, timeout=5.0).json()

def export_metric(node_url, bus_key):
    return requests.post(f"{node_url}/instruction", json={"gate": "export_tensor_metric", "bus_key": bus_key}, timeout=5.0).json()

def build_n_ghz_state(nodes):
    """ 🌟 N 體微觀張量編織 (無補丁原汁原味) """
    reset_cluster(nodes)
    N = len(nodes)

    # 1. Node 0 施加 Hadamard 門並導出 Metric
    apply_gate(nodes[0], "h")
    export_metric(nodes[0], "hsq:node:0:metric")

    # 2. 依序對 Node 1 ~ N-1 執行 CNOT 級聯鎖定
    for i in range(1, N):
        prev_key = f"hsq:node:{i-1}:metric"
        curr_key = f"hsq:node:{i}:metric"
        
        apply_gate(nodes[i], "cnot_interlock", source_bus_key=prev_key)
        export_metric(nodes[i], curr_key)

    # 3. 觸發微觀場微幅演化 (可調噪聲)
    for url in nodes:
        requests.post(f"{url}/evolve", json={"t": 0.05, "noise": 0.0}, timeout=5.0)

def measure_n_basis(nodes, basis_str):
    """
    對 N 顆容器進行投影測量：
    - X 基底: H 門
    - Y 基底: 原生 Y 門 + H 門
    - Z 基底: 不做旋轉
    """
    N = len(nodes)
    for i in range(N):
        b = basis_str[i]
        url = nodes[i]
        if b == "X":
            apply_gate(url, "h")
        elif b == "Y":
            apply_gate(url, "y")
            apply_gate(url, "h")

    # 讀取每顆容器原生的狀態振幅 (a, b)
    amplitudes = []
    for i in range(N):
        res = export_metric(nodes[i], f"hsq:node:{i}:meas")
        a = complex(*res["state_a"])
        b = complex(*res["state_b"])
        amplitudes.append((a, b))

    # 物理正交投影計算 2^N 個基態機率 (零 post-processing)
    all_bitstrings = ["".join(seq) for seq in itertools.product("01", repeat=N)]
    probs = {}
    
    for bitstr in all_bitstrings:
        amplitude = 1.0 + 0j
        for qubit_idx, bit in enumerate(bitstr):
            a_val, b_val = amplitudes[qubit_idx]
            amplitude *= (b_val if bit == "1" else a_val)
        probs[bitstr] = np.abs(amplitude)**2

    total_p = sum(probs.values())
    if total_p > 0:
        probs = {k: v / total_p for k, v in probs.items()}

    # 宇稱計算: P_even - P_odd
    p_even = sum(prob for b_str, prob in probs.items() if b_str.count("1") % 2 == 0)
    p_odd = sum(prob for b_str, prob in probs.items() if b_str.count("1") % 2 != 0)

    return p_even - p_odd

def execute_mermin_n_qubits(n_qubits: int):
    nodes = get_node_urls(n_qubits)
    print(f"\n==================================================")
    print(f"🚀 N={n_qubits} 顆 HSQ 容器原初 Mermin-GHZ 糾纏維度測試")
    print(f"==================================================")

    # 1. 全 X 測量: <X...X>
    build_n_ghz_state(nodes)
    exp_all_x = measure_n_basis(nodes, "X" * n_qubits)
    print(f"  <{'X'*n_qubits}> 期望值: {exp_all_x:+.6f} (理論值: +1.0)")

    # 2. 奇數個 Y 的 Mermin 多體算符測試 (例如 X...XYY, X...YXY 等)
    y_pairs = []
    for p in range(1, n_qubits, 2):  # 1, 3, 5... 個 Y
        for combo in itertools.combinations(range(n_qubits), p):
            b_list = ["X"] * n_qubits
            for idx in combo:
                b_list[idx] = "Y"
            y_pairs.append("".join(b_list))

    total_mermin_sum = exp_all_x
    print(f"\n  --- 多體 Y-基底干涉投影 (共 {len(y_pairs)} 種組合) ---")
    
    for basis in y_pairs:
        build_n_ghz_state(nodes)
        val = measure_n_basis(nodes, basis)
        total_mermin_sum -= val  # 扣除奇數 Y 的相角
        print(f"  <{basis}> 期望值: {val:+.6f}")

    theoretical_qm_limit = 2**(n_qubits - 1)
    classical_lhv_limit = 2**( (n_qubits - 1) // 2 )

    print("--------------------------------------------------------")
    print(f"🎯 N={n_qubits} 算符總期望值 <M>: {total_mermin_sum:+.6f}")
    print(f"   古典局域隱變數 (LHV) 極限: <= {classical_lhv_limit:.1f}")
    print(f"   量子力學理論極限 (QM)   : = +{theoretical_qm_limit:.1f}")

if __name__ == "__main__":
    # 可直接測試 N = 4 顆容器的 GHZ 糾纏態
    execute_mermin_n_qubits(n_qubits=5)
