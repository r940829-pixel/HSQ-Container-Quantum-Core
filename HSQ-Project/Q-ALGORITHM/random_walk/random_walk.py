# ==============================================================================
# HSQ V6.0 ABLATION DRIVER: HSQ CONTINUOUS FIELD Walk vs QISKIT DTQW
# [FULL COMPATIBILITY WITH HSQ V6.0 UNIVERSAL GATE & PHASE CHAIN API]
# ==============================================================================

import os
import sys
import time
import datetime
import hashlib
import argparse
from typing import Optional, Dict, Any

import numpy as np
import requests
import matplotlib
try:
    matplotlib.use('Agg')
except Exception:
    pass
import matplotlib.pyplot as plt
from scipy import stats

print("======================================================================")
print("===   HSQ v6.0 Spinor Model vs Qiskit DTQW: Ablation Driver Driver  ===")
print("======================================================================")


class HSQv6LiveWalker:
    def __init__(self, target_address: str, name: str = "HSQ-v6-Node"):
        self.url = f"http://{target_address}"
        self.name = name

    def check_live_handshake(self) -> bool:
        try:
            res = requests.get(f"{self.url}/ping", timeout=1.5)
            if res.status_code == 200 and res.json().get("status") == "ready":
                return True
        except Exception:
            pass
        return False

    def force_reset(self) -> bool:
        try:
            res = requests.post(f"{self.url}/reset", json={}, timeout=1.0)
            return res.status_code == 200
        except Exception:
            return False

    def fetch_live_wavefront(self, steps: int, config_id: str, seed_val: int, 
                             noise_level: float, phase_delta: float) -> Optional[np.ndarray]:
        """
        利用 HSQ v6.0 API 執行硬體/模擬器相干演化並擷取 512 空間點機率密度
        """
        custom_headers = {"Connection": "close", "Content-Type": "application/json"}
        self.force_reset()

        try:
            # 1. Coin 準備：作用 Hadamard 門
            r_h = requests.post(f"{self.url}/instruction", json={"gate": "h"}, headers=custom_headers, timeout=1.0)
            if r_h.status_code != 200:
                return None

            # 2. Phase 注入 (對應 Config B 與 D)
            if config_id in ["B", "D"]:
                r_p = requests.post(
                    f"{self.url}/instruction", 
                    json={"gate": "phase", "delta_phi": float(phase_delta)}, 
                    headers=custom_headers, 
                    timeout=1.0
                )
                if r_p.status_code != 200:
                    return None

            # 3. 空間場演化 (Step-by-Step Evolve)
            final_density = None
            for step_idx in range(steps):
                payload = {
                    "noise": float(noise_level),
                    "seed": int(seed_val) + int(step_idx),
                    "t": 0.1,
                    "grid_size": 512
                }
                res = requests.post(f"{self.url}/evolve", json=payload, headers=custom_headers, timeout=1.5)
                if res.status_code != 200:
                    return None
                
                # 取得 HSQ v6.0 計算出的 512 空間點機率分佈
                prob_data = res.json().get('probability_density')
                if prob_data:
                    final_density = np.array(prob_data, dtype=float)

            return final_density

        except Exception as e:
            return None


def simulate_qiskit_dtqw(steps: int, config_id: str, discrete_lattice: np.ndarray, 
                         phase_delta: float, noise_level: float = 0.0) -> np.ndarray:
    """ 10-Qubit Hadamard-coin DTQW (Qiskit Aer Simulator) """
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error

    num_position_qubits = 9
    total_qubits = num_position_qubits + 1
    coin_idx = num_position_qubits

    qc = QuantumCircuit(total_qubits)
    init_position = 256
    for q in range(num_position_qubits):
        if (init_position >> q) & 1:
            qc.x(q)

    # Coin 態初始化
    qc.h(coin_idx)
    qc.s(coin_idx)
    if config_id in ["B", "D"]:
        qc.p(float(phase_delta), coin_idx)

    # DTQW 位移演化
    for _ in range(steps):
        qc.h(coin_idx)
        # 右移 (Shift Right)
        for q in range(num_position_qubits - 1, -1, -1):
            control_qubits = list(range(q)) + [coin_idx]
            if len(control_qubits) == 1:
                qc.cx(control_qubits[0], q)
            else:
                qc.mcx(control_qubits[:-1], q, ctrl_state='1'*len(control_qubits[:-1]))
        
        # 左移 (Shift Left)
        qc.x(coin_idx)
        for q in range(num_position_qubits):
            qc.x(q)
        for q in range(num_position_qubits - 1, -1, -1):
            control_qubits = list(range(q)) + [coin_idx]
            if len(control_qubits) == 1:
                qc.cx(control_qubits[0], q)
            else:
                qc.mcx(control_qubits[:-1], q, ctrl_state='1'*len(control_qubits[:-1]))
        for q in range(num_position_qubits):
            qc.x(q)
        qc.x(coin_idx)

    # 噪聲模型 (Depolarizing Noise)
    noise_model = NoiseModel()
    if noise_level > 0.0:
        error_gate = depolarizing_error(noise_level * 0.05, 1)
        error_gate_2q = depolarizing_error(noise_level * 0.1, 2)
        noise_model.add_all_qubit_quantum_error(error_gate, ["h", "x", "p", "s"])
        noise_model.add_all_qubit_quantum_error(error_gate_2q, ["cx", "mcx"])

    qc.measure_all()
    simulator = AerSimulator(noise_model=noise_model)
    qc_compiled = transpile(qc, simulator)

    shots = 20000
    result = simulator.run(qc_compiled, shots=shots).result()
    counts = result.get_counts(qc_compiled)

    qiskit_raw_probs = np.zeros(512)
    for state_str, count_val in counts.items():
        clean_bin = state_str.replace(" ", "")[-total_qubits:]
        pos_val = int(clean_bin[1:], 2)
        qiskit_raw_probs[pos_val] += count_val

    prob_mesh = np.zeros(len(discrete_lattice))
    for idx, lat_val in enumerate(discrete_lattice):
        prob_mesh[idx] = qiskit_raw_probs[int(lat_val)]

    return prob_mesh / (prob_mesh.sum() + 1e-12)


def quantify_metrics(p_mesh: np.ndarray, q_ideal: np.ndarray):
    """ 計算 Fidelity, TVD, Symmetry Index, Peak-to-Valley Ratio """
    if p_mesh is None or np.sum(p_mesh) == 0:
        return 0.0, 1.0, 0.0, 0.0

    p_full = np.clip(p_mesh, 1e-12, 1.0) / np.sum(p_mesh)
    q_full = np.clip(q_ideal, 1e-12, 1.0) / np.sum(q_ideal)

    fidelity = (np.sum(np.sqrt(p_full * q_full))) ** 2
    tvd = 0.5 * np.sum(np.abs(p_full - q_full))

    mid_point = len(p_full) // 2
    m_l, m_r = float(np.sum(p_full[:mid_point])), float(np.sum(p_full[mid_point:]))
    symmetry = 1.0 - (abs(m_l - m_r) / (m_l + m_r + 1e-12))
    peak_valley_ratio = float(np.max(p_full)) / (p_full[mid_point] + 1e-12)

    return float(fidelity), float(tvd), float(symmetry), float(peak_valley_ratio)


def normalize_density(raw_density: np.ndarray, discrete_lattice: np.ndarray) -> np.ndarray:
    if raw_density is None or len(raw_density) != len(discrete_lattice):
        return np.zeros(len(discrete_lattice))
    return np.abs(raw_density) / (np.sum(np.abs(raw_density)) + 1e-12)


def light_cone_leakage(p_mesh: np.ndarray, steps: int, origin: int = 256) -> float:
    """ 計算超出光錐 (Light Cone) 的機率質分比 """
    if p_mesh is None or np.sum(p_mesh) == 0:
        return float('nan')
    p = np.asarray(p_mesh, float)
    p = p / p.sum()
    lo, hi = origin - int(steps), origin + int(steps)
    out = 0.0
    if lo > 0:
        out += p[:lo].sum()
    if hi + 1 < len(p):
        out += p[hi+1:].sum()
    return float(out)


def process_and_pairwise_test(loaded_dict: dict, discrete_lattice: np.ndarray, 
                              steps: int, phase_delta: float, noise_level: float):
    matrix_store = loaded_dict["matrix_store"]

    _refs = loaded_dict.get("stored_references")
    if _refs:
        print("ℹ️ [offline] Using Qiskit references stored in dataset (.npy)")
        q_ref_A, q_ref_B = np.asarray(_refs["q_ref_A"]), np.asarray(_refs["q_ref_B"])
    else:
        q_ref_A = simulate_qiskit_dtqw(steps, "A", discrete_lattice, phase_delta, noise_level=noise_level)
        q_ref_B = simulate_qiskit_dtqw(steps, "B", discrete_lattice, phase_delta, noise_level=noise_level)

    if _refs and "q_ideal_A" in _refs:
        q_ideal_A = np.asarray(_refs["q_ideal_A"])
    else:
        q_ideal_A = simulate_qiskit_dtqw(steps, "A", discrete_lattice, phase_delta, noise_level=0.0)

    configs_meta = [
        ("A", "Config A: Qiskit DTQW (self-consistency check, phase off)", q_ref_A),
        ("B", "Config B: Qiskit DTQW (self-consistency check, phase on)", q_ref_B),
        ("C", "Config C: HSQ v6.0 Continuous Field Model (phase off)", q_ref_A),
        ("D", "Config D: HSQ v6.0 Continuous Field Model (phase on)", q_ref_B)
    ]

    table_3_rows = []
    f_channels = {}

    for cid, name, q_ref in configs_meta:
        raw_list = matrix_store[cid]
        valid_rows = []
        for row in raw_list:
            if row is not None and np.sum(np.abs(row)) > 0:
                resampled = normalize_density(row, discrete_lattice)
                valid_rows.append(resampled)

        raw_metrics = []
        fidelities_vector = []
        for row in valid_rows:
            fid, tvd, sym, pvr = quantify_metrics(row, q_ref)
            raw_metrics.append([fid, tvd, sym, pvr])
            fidelities_vector.append(fid)

        f_channels[cid] = np.array(fidelities_vector) if fidelities_vector else np.zeros(1)
        metrics_arr = np.array(raw_metrics) if raw_metrics else np.zeros((1, 4))

        means = np.mean(metrics_arr, axis=0)
        stds = np.std(metrics_arr, axis=0, ddof=1) if len(metrics_arr) > 1 else np.zeros(4)

        table_3_rows.append([
            name,
            f"{means[0]*100:.2f}% ± {stds[0]*100:.2f}%",
            f"{means[1]:.4f} ± {stds[1]:.4f}",
            f"{means[2]:.4f} ± {stds[2]:.4f}",
            f"{means[3]:.2f} ± {stds[3]:.2f}"
        ])

    print("\n======================================================================")
    print("[Pairwise Equivalence Tests (TOST) - 512 Lattice]")
    print("======================================================================")

    def run_tost_comparison(f1, f2, hypothesis_title, epsilon=0.005):
        n1, n2 = len(f1), len(f2)
        mean_delta = f1.mean() - f2.mean()
        v1, v2 = np.var(f1, ddof=1), np.var(f2, ddof=1)
        se = np.sqrt(v1/n1 + v2/n2)
        degenerate = (v1 < 1e-24) or (v2 < 1e-24) or (se < 1e-12)

        if degenerate:
            print(f" -> [{hypothesis_title}] DEGENERATE: Zero variance; TOST not applicable.")
            return [hypothesis_title, f"{mean_delta:+.4e}", "n/a", "n/a (zero variance)", f"Bound=+/-{epsilon}", "Not testable"]

        df = (v1/n1 + v2/n2)**2 / ((v1/n1)**2/(n1-1) + (v2/n2)**2/(n2-1))
        t_crit = stats.t.ppf(0.975, df=df)
        t1 = (mean_delta - (-epsilon)) / se
        t2 = (mean_delta - epsilon) / se
        p1 = 1 - stats.t.cdf(t1, df=df)
        p2 = stats.t.cdf(t2, df=df)
        p_tost = max(p1, p2)

        verdict = "Equivalence established" if p_tost < 0.05 else "Equivalence NOT established"
        print(f" -> TOST bound [+/-{epsilon*100}%] | [{hypothesis_title}]: p_tost = {p_tost:.4f} -> {verdict}")
        return [hypothesis_title, f"{mean_delta:+.4e}", f"t-crit={t_crit:.3f}", f"p_tost={p_tost:.4f}", f"Bound=+/-{epsilon}", verdict]

    row_hsq = run_tost_comparison(f_channels["C"], f_channels["D"], "HSQ v6.0 Phase Off vs On (C vs D)")
    row_backend = run_tost_comparison(f_channels["A"], f_channels["C"], "Qiskit DTQW vs HSQ v6.0 Model (A vs C)")

    # 數據與圖表輸出
    hsq_C_mean = np.mean([normalize_density(r, discrete_lattice) for r in matrix_store["C"] if r is not None], axis=0)
    qis_A_mean = np.mean([normalize_density(r, discrete_lattice) for r in matrix_store["A"] if r is not None], axis=0)
    leak_hsq = light_cone_leakage(hsq_C_mean, steps)
    leak_qis = light_cone_leakage(qis_A_mean, steps)
    _, _, _, pvr_hsq = quantify_metrics(hsq_C_mean, q_ideal_A)
    _, _, _, pvr_qis = quantify_metrics(qis_A_mean, q_ideal_A)
    fid_hsq_vs_ideal = float(np.mean([quantify_metrics(normalize_density(r, discrete_lattice), q_ideal_A)[0] for r in matrix_store['C'] if r is not None]))
    gap = f_channels['A'].mean() - f_channels['C'].mean()

    with open("tables_report.txt", "w", encoding="utf-8") as f:
        f.write(f"HSQ v6.0 Model vs Qiskit DTQW  |  steps={steps}  noise={noise_level}\n")
        f.write("=" * 72 + "\n")
        f.write("PRIMARY RESULT - Accuracy of HSQ v6.0 Model\n")
        f.write(f"  Config C Fidelity vs Qiskit DTQW Reference : {f_channels['C'].mean()*100:.2f}%\n")
        f.write(f"  Config C Fidelity vs NOISELESS Ideal DTQW  : {fid_hsq_vs_ideal*100:.2f}%\n\n")
        f.write("FALSIFICATION METRICS\n")
        f.write(f"  Light-cone Leakage, HSQ v6.0 : {leak_hsq:.4f}\n")
        f.write(f"  Light-cone Leakage, Qiskit   : {leak_qis:.4f}\n")
        f.write(f"  Peak-to-Valley Ratio, HSQ    : {pvr_hsq:.2f}\n")
        f.write(f"  Peak-to-Valley Ratio, Qiskit : {pvr_qis:.2f}\n\n")
        f.write("DISAGREEMENT GAP\n")
        f.write(f"  Gap = F(Qiskit) - F(HSQ) = {gap:.4f} ({gap*100:.2f}%)\n")

    # 繪製消融圖表 (Figure 2)
    fig_qrw, ax_qrw = plt.subplots(figsize=(10, 5))
    ax_qrw.bar(discrete_lattice, q_ideal_A, width=0.6, color='#2C3E50', alpha=0.25, label='Ideal Pure Qiskit (Q)')
    ax_qrw.step(discrete_lattice, hsq_C_mean, where='mid', color='#9B59B6', linewidth=2.0, label='Config C: HSQ v6.0 Continuous Model')
    ax_qrw.plot(discrete_lattice, qis_A_mean, color='#E67E22', linestyle='-.', marker='o', markersize=2, alpha=0.8, label='Config A: Qiskit DTQW (Noisy)')

    ax_qrw.set_xlabel('Discrete Spatial Lattice Site Index (512-Grid Range)', fontsize=11)
    ax_qrw.set_ylabel('Probability Density P(x)', fontsize=11)
    ax_qrw.set_xlim(256 - 3.2*steps, 256 + 3.2*steps)

    for edge in (256 - steps, 256 + steps):
        ax_qrw.axvline(edge, color='#C0392B', linestyle='--', linewidth=1.2, alpha=0.9)
    ax_qrw.axvline(256 - steps, color='#C0392B', linestyle='--', linewidth=1.2, alpha=0.9, label=f'DTQW Light Cone (Origin ± {steps})')

    ax_qrw.grid(True, linestyle=':', alpha=0.4)
    ax_qrw.legend(loc='upper right', frameon=True, fontsize=9.5)
    plt.title(f"HSQ v6.0 Spinor Model vs Qiskit DTQW (steps={steps}, noise={noise_level})", fontsize=10, fontweight='bold')
    plt.savefig("fig2_qrw_ablation_profile.png", dpi=300, bbox_inches='tight')
    plt.close()

    print("✅ [Done] Ablation report and profile saved cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HSQ v6.0 Ablation Driver Controller")
    parser.add_argument("--seeds", type=int, default=20, help="Number of Monte Carlo Seeds")
    parser.add_argument("--steps", type=int, default=10, help="Evolution Steps")
    parser.add_argument("--noise", type=float, default=0.00, help="Thermal Noise Level")
    parser.add_argument("--phase", type=float, default=0.05, help="Global Phase Shift")
    parser.add_argument("--target-ip", type=str, default="127.0.0.1", help="HSQ v6.0 Node IP Address")
    parser.add_argument("--port", type=int, default=5011, help="HSQ v6.0 Node Port")
    parser.add_argument("--analyze-only", type=str, default=None, help="Offline .npy analysis")

    args = parser.parse_args()

    lattice_axis = np.arange(512)

    if args.analyze_only:
        payload = np.load(args.analyze_only, allow_pickle=True).item()
        process_and_pairwise_test(
            payload, 
            discrete_lattice=lattice_axis,
            steps=int(payload["steps"]), 
            phase_delta=float(payload["phase_delta"]),
            noise_level=float(payload["target_noise"])
        )
        sys.exit(0)

    target_address = f"{args.target_ip}:{args.port}"
    hsq_node = HSQv6LiveWalker(target_address, "HSQ-v6-Node")

    print(f"\n[STAGE 1] Testing active handshake with HSQ v6.0 Node at {target_address}...")
    if not hsq_node.check_live_handshake():
        print(f"❌ [Fatal Error] Cannot ping HSQ v6.0 Node at {target_address}. Please verify container.")
        sys.exit(1)
    print("✅ Handshake successful.")

    print(f"\n[STAGE 2] Executing heterogeneous benchmarking loops ({args.steps} steps)...")
    matrix_store = {"A": [], "B": [], "C": [], "D": []}
    seed_list = []

    for seed in range(args.seeds):
        current_seed = 1000 + seed

        wf_A = simulate_qiskit_dtqw(args.steps, "A", lattice_axis, args.phase, noise_level=args.noise)
        wf_B = simulate_qiskit_dtqw(args.steps, "B", lattice_axis, args.phase, noise_level=args.noise)
        wf_C = hsq_node.fetch_live_wavefront(args.steps, "C", current_seed, args.noise, args.phase)
        wf_D = hsq_node.fetch_live_wavefront(args.steps, "D", current_seed, args.noise, args.phase)

        if (wf_A is None) or (wf_B is None) or (wf_C is None) or (wf_D is None):
            print(f" ⚠️ [Timeout/Fail] Seed {current_seed} failed. Skipping.")
            continue

        matrix_store["A"].append(wf_A)
        matrix_store["B"].append(wf_B)
        matrix_store["C"].append(wf_C)
        matrix_store["D"].append(wf_D)
        seed_list.append(current_seed)
        print(f" -> Secured Seed {current_seed:<4} | Verified Normalization ≈ 1.0")

    file_name = f"matrix_store_noise_{args.noise:.2f}.npy"
    ref_payload = {
        "q_ref_A": simulate_qiskit_dtqw(args.steps, "A", lattice_axis, args.phase, noise_level=args.noise),
        "q_ref_B": simulate_qiskit_dtqw(args.steps, "B", lattice_axis, args.phase, noise_level=args.noise),
        "q_ideal_A": simulate_qiskit_dtqw(args.steps, "A", lattice_axis, args.phase, noise_level=0.0),
    }

    metadata_payload = {
        "matrix_store": matrix_store,
        "stored_references": ref_payload,
        "seed_list": seed_list,
        "target_noise": args.noise,
        "steps": args.steps,
        "phase_delta": args.phase,
        "execution_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    np.save(file_name, metadata_payload, allow_pickle=True)
    print(f"\n🏆 [Dataset Secured] Saved benchmarking data to {file_name}")

    print("\n[STAGE 3] Performing statistical equivalence analysis...")
    process_and_pairwise_test(metadata_payload, discrete_lattice=lattice_axis, steps=args.steps, phase_delta=args.phase, noise_level=args.noise)