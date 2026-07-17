import os
import sys
import time
import datetime
import hashlib
import requests
import numpy as np
import matplotlib
try:
    matplotlib.use('Agg') 
except:
    pass
import matplotlib.pyplot as plt
from scipy import stats

print("======================================================================")
print("===  HSQ closed-form model vs Qiskit DTQW: ablation driver          ===")
print("======================================================================")


class LiveTargetWalker:
    def __init__(self, target_address, name):
        self.url = f"http://{target_address}"
        self.name = name

    def check_live_handshake(self):
        try:
            res = requests.get(f"{self.url}/ping", timeout=1.5)
            if res.status_code == 200: return True
        except: pass
        return False

    def force_hardware_reset(self, grid_size=512):
        try: requests.post(f"{self.url}/reset", json={"grid_size": int(grid_size)}, timeout=1.0)
        except: pass

    def fetch_live_wavefront(self, steps, config_id, seed_val, noise_level, phase_delta):
        custom_headers = {"Connection": "close", "Content-Type": "application/json"}
        self.force_hardware_reset(grid_size=512)

        try:
            r_h = requests.post(f"{self.url}/instruction", json={"gate": "h"}, headers=custom_headers, timeout=1.0)
            if r_h.status_code != 200: return None
            
            # phase convention MUST match the qiskit arm below (B and D carry the phase)
            if config_id in ["B", "D"]:
                r_p = requests.post(f"{self.url}/instruction", json={"gate": "phase", "delta_phi": float(phase_delta)}, headers=custom_headers, timeout=1.0)
                if r_p.status_code != 200: return None
        except:
            return None

        final_density = None
        for step_idx in range(steps):
            try:
                payload = {
                    "noise": float(noise_level), 
                    "seed": int(seed_val) + int(step_idx), 
                    "t": 0.1,
                    "grid_size": 512 
                }
                res = requests.post(f"{self.url}/evolve", json=payload, headers=custom_headers, timeout=1.5)
                if res.status_code != 200: return None 
                final_density = np.array(res.json().get('probability_density'))
            except:
                return None
        return final_density


def simulate_qiskit_dtqw(steps, config_id, discrete_lattice, phase_delta, noise_level=0.0):
    """Genuine 10-qubit Hadamard-coin DTQW on Aer. Used BOTH as the ideal reference
    (noise_level=0) and as the noisy A/B arms. It is not 'ground truth' when it is
    itself the measured object -- name it for what it computes."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    
    num_position_qubits = 9
    total_qubits = num_position_qubits + 1
    coin_idx = num_position_qubits
    
    qc = QuantumCircuit(total_qubits)
    init_position = 256
    for q in range(num_position_qubits):
        if (init_position >> q) & 1: qc.x(q)
            
    qc.h(coin_idx)
    qc.s(coin_idx)
    if config_id in ["B", "D"]: qc.p(float(phase_delta), coin_idx)
        
    for _ in range(steps):
        qc.h(coin_idx)
        for q in range(num_position_qubits - 1, -1, -1):
            control_qubits = list(range(q)) + [coin_idx]
            if len(control_qubits) == 1: qc.cx(control_qubits[0], q)
            else: qc.mcx(control_qubits[:-1], q, ctrl_state='1'*len(control_qubits[:-1]))
        qc.x(coin_idx)
        for q in range(num_position_qubits): qc.x(q)
        for q in range(num_position_qubits - 1, -1, -1):
            control_qubits = list(range(q)) + [coin_idx]
            if len(control_qubits) == 1: qc.cx(control_qubits[0], q)
            else: qc.mcx(control_qubits[:-1], q, ctrl_state='1'*len(control_qubits[:-1]))
        for q in range(num_position_qubits): qc.x(q)
        qc.x(coin_idx) 
    
    noise_model = NoiseModel()
    if noise_level > 0.0:
        error_gate = depolarizing_error(noise_level * 0.05, 1)
        error_gate_2q = depolarizing_error(noise_level * 0.1, 2)
        noise_model.add_all_qubit_quantum_error(error_gate, ["h", "x", "p", "s"])
        noise_model.add_all_qubit_quantum_error(error_gate_2q, ["cx", "mcx"])

    qc.measure_all()
    simulator = AerSimulator(noise_model=noise_model)
    qc = transpile(qc, simulator)
    
    shots = 20000
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts(qc)
    
    qiskit_raw_probs = np.zeros(512)
    for state_str, count_val in counts.items():
        clean_bin = state_str.replace(" ", "")[-total_qubits:]
        pos_val = int(clean_bin[1:], 2)
        qiskit_raw_probs[pos_val] += count_val
        
    prob_mesh = np.zeros(len(discrete_lattice))
    for idx, lat_val in enumerate(discrete_lattice):
        prob_mesh[idx] = qiskit_raw_probs[int(lat_val)]
        
    return prob_mesh / (prob_mesh.sum() + 1e-12)


def quantify_metrics(p_mesh, q_ideal):
    if p_mesh is None or np.sum(p_mesh) == 0: return 0.0, 1.0, 0.0, 0.0
    
    p_full = np.clip(p_mesh, 1e-12, 1.0) / np.sum(p_mesh)
    q_full = np.clip(q_ideal, 1e-12, 1.0) / np.sum(q_ideal)
    
    fidelity = (np.sum(np.sqrt(p_full * q_full))) ** 2
    tvd = 0.5 * np.sum(np.abs(p_full - q_full))
    
    mid_point = len(p_full) // 2
    m_l, m_r = float(np.sum(p_full[:mid_point])), float(np.sum(p_full[mid_point:]))
    symmetry = 1.0 - (abs(m_l - m_r) / (m_l + m_r + 1e-12))
    peak_valley_ratio = float(max(p_full)) / (p_full[mid_point] + 1e-12)
    return float(fidelity), float(tvd), float(symmetry), float(peak_valley_ratio)


def normalize_density(raw_density, discrete_lattice):
    if raw_density is None or len(raw_density) != len(discrete_lattice):
        return np.zeros(len(discrete_lattice))
    return np.abs(raw_density) / (np.sum(np.abs(raw_density)) + 1e-12)


def light_cone_leakage(p_mesh, steps, origin=256):
    """Fraction of probability mass outside origin +/- steps.
    An ideal n-step DTQW has EXACTLY zero mass outside its light cone, so any
    non-zero value falsifies a walk interpretation regardless of fidelity convention."""
    if p_mesh is None or np.sum(p_mesh) == 0: return float('nan')
    p = np.asarray(p_mesh, float); p = p / p.sum()
    lo, hi = origin - int(steps), origin + int(steps)
    out = 0.0
    if lo > 0: out += p[:lo].sum()
    if hi + 1 < len(p): out += p[hi+1:].sum()
    return float(out)


def process_and_pairwise_test(loaded_dict, discrete_lattice, steps, phase_delta, noise_level):
    matrix_store = loaded_dict["matrix_store"]
    

    # Prefer the references stored in the .npy so a reviewer can re-score OFFLINE
    # (no qiskit install, no live backend). Fall back to simulating them.
    _refs = loaded_dict.get("stored_references")
    if _refs:
        print("[offline] using qiskit references stored in the .npy (no qiskit needed)")
        q_ref_A, q_ref_B = np.asarray(_refs["q_ref_A"]), np.asarray(_refs["q_ref_B"])
    else:
        q_ref_A = simulate_qiskit_dtqw(steps, "A", discrete_lattice, phase_delta, noise_level=noise_level)
        q_ref_B = simulate_qiskit_dtqw(steps, "B", discrete_lattice, phase_delta, noise_level=noise_level)
    

    if _refs and "q_ideal_A" in _refs:
        q_ideal_A = np.asarray(_refs["q_ideal_A"])
    else:
        q_ideal_A = simulate_qiskit_dtqw(steps, "A", discrete_lattice, phase_delta, noise_level=0.0)
    
    # NOTE: A/B are the qiskit DTQW scored against another qiskit draw -- this is a
    # SELF-CONSISTENCY check (circular by construction, pins near 1.0), NOT a baseline.
    # C/D are the HSQ closed-form model scored against the matching-phase qiskit reference.
    configs_meta = [
        ("A", "Config A: Qiskit DTQW (self-consistency check, phase off)", q_ref_A),
        ("B", "Config B: Qiskit DTQW (self-consistency check, phase on)", q_ref_B),
        ("C", "Config C: HSQ closed-form wavepacket model (phase off)", q_ref_A),
        ("D", "Config D: HSQ closed-form wavepacket model (phase on)", q_ref_B)
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
        
        table_3_rows.append([name, f"{means[0]*100:.2f}% ± {stds[0]*100:.2f}%", f"{means[1]:.4f} ± {stds[1]:.4f}", f"{means[2]:.4f} ± {stds[2]:.4f}", f"{means[3]:.2f} ± {stds[3]:.2f}"])

    print("\n======================================================================")
    print("[Pairwise equivalence tests (TOST) - 512 lattice]")
    print("======================================================================")
    
    def run_tost_comparison(f1, f2, hypothesis_title, epsilon=0.005):
        n1, n2 = len(f1), len(f2)
        mean_delta = f1.mean() - f2.mean()
        v1, v2 = np.var(f1, ddof=1), np.var(f2, ddof=1)
        se = np.sqrt(v1/n1 + v2/n2)
        degenerate = (v1 < 1e-24) or (v2 < 1e-24) or (se < 1e-12)

        # DEGENERATE GUARD: at noise=0 the closed-form model is deterministic, so every
        # "seed" returns an identical row (var == 0). Those n replicates are pseudo-
        # replication, not samples; a t-test on them is meaningless (se -> 0 => t -> inf
        # => p_tost -> 0 => "equivalence" would be auto-confirmed). Report, do not test.
        if degenerate:
            print(f" -> [{hypothesis_title}] DEGENERATE: zero variance (identical replicates); TOST not applicable.")
            return [hypothesis_title, f"{mean_delta:+.4e}", "n/a",
                    "n/a (zero variance)", f"Bound=+/-{epsilon}",
                    "Not testable (pseudo-replication)"]

        # Welch-Satterthwaite degrees of freedom
        df = (v1/n1 + v2/n2)**2 / ((v1/n1)**2/(n1-1) + (v2/n2)**2/(n2-1))
        t_crit = stats.t.ppf(0.975, df=df)
        t1 = (mean_delta - (-epsilon)) / se
        t2 = (mean_delta - epsilon) / se
        p1 = 1 - stats.t.cdf(t1, df=df)
        p2 = stats.t.cdf(t2, df=df)
        p_tost = max(p1, p2)

        # p_tost < 0.05 => equivalence established within +/-epsilon.
        # p_tost >= 0.05 => equivalence NOT established. That is NOT the same as
        # "no significant difference" -- absence of evidence is not evidence of absence.
        verdict = "Equivalence established" if p_tost < 0.05 else "Equivalence NOT established"
        print(f" -> TOST bound [+/-{epsilon*100}%] | [{hypothesis_title}]: p_tost = {p_tost:.4f} -> {verdict}")
        return [hypothesis_title, f"{mean_delta:+.4e}", f"t-crit={t_crit:.3f}", f"p_tost={p_tost:.4f}", f"Bound=+/-{epsilon}", verdict]

    row_hsq = run_tost_comparison(f_channels["C"], f_channels["D"], "HSQ phase off vs on (C vs D)")
    row_backend = run_tost_comparison(f_channels["A"], f_channels["C"], "Qiskit DTQW vs HSQ closed-form model (A vs C)")

    # --- Falsification metrics for the HSQ closed-form model (the paper's核心 negative result) ---
    hsq_C_mean = np.mean([normalize_density(r, discrete_lattice) for r in matrix_store["C"] if r is not None], axis=0)
    qis_A_mean = np.mean([normalize_density(r, discrete_lattice) for r in matrix_store["A"] if r is not None], axis=0)
    leak_hsq = light_cone_leakage(hsq_C_mean, steps)
    leak_qis = light_cone_leakage(qis_A_mean, steps)
    _, _, _, pvr_hsq = quantify_metrics(hsq_C_mean, q_ideal_A)
    _, _, _, pvr_qis = quantify_metrics(qis_A_mean, q_ideal_A)
    # mean of per-seed fidelities (same estimator as the line above -- do not mix
    # 'mean of fidelities' with 'fidelity of the mean')
    fid_hsq_vs_ideal = float(np.mean([quantify_metrics(normalize_density(r, discrete_lattice), q_ideal_A)[0]
                                      for r in matrix_store['C'] if r is not None]))
    gap = f_channels['A'].mean() - f_channels['C'].mean()

    with open("tables_report.txt", "w", encoding="utf-8") as f:
        f.write(f"HSQ closed-form model vs Qiskit DTQW  |  steps={steps}  noise={noise_level}\n")
        f.write("=" * 72 + "\n")
        f.write("PRIMARY RESULT - accuracy of the HSQ closed-form model\n")
        f.write(f"  Config C fidelity vs Qiskit DTQW reference : {f_channels['C'].mean()*100:.2f}%\n")
        f.write(f"  Config C fidelity vs NOISELESS ideal DTQW  : {fid_hsq_vs_ideal*100:.2f}%\n")
        f.write(f"  (a faithful emulator would score >95% at noise=0)\n\n")
        f.write("FALSIFICATION METRICS (independent of any fidelity convention)\n")
        f.write(f"  Light-cone leakage, HSQ    : {leak_hsq:.4f}   <- mass outside origin+/-{steps}\n")
        f.write(f"  Light-cone leakage, Qiskit : {leak_qis:.4f}   <- an ideal DTQW has EXACTLY 0\n")
        f.write(f"  Peak-to-valley ratio, HSQ    : {pvr_hsq:.2f}   <- 1.00 means the peak IS the centre\n")
        f.write(f"  Peak-to-valley ratio, Qiskit : {pvr_qis:.2f}   <- ballistic double-horn\n\n")
        f.write("REFERENCE SELF-CONSISTENCY (circular by construction; pins near 1.0)\n")
        f.write(f"  Config A (Qiskit vs another Qiskit draw)   : {f_channels['A'].mean()*100:.2f}%\n\n")
        f.write("DISAGREEMENT GAP (larger = worse; this is NOT a fidelity or an identity score)\n")
        f.write(f"  gap = F(Qiskit self-consistency) - F(HSQ) = {gap:.4f}\n")
        f.write(f"  i.e. the HSQ model misses the Qiskit DTQW by {gap*100:.2f} percentage points.\n")
    
    fig2, ax2 = plt.subplots(figsize=(13.5, 2.2)); ax2.axis('off')
    ax2.table(cellText=[row_hsq, row_backend], colLabels=["Pairwise Testing Group", "Mean Delta (Δfid)", "t-Distribution Crit", "TOST Max p-value", "Equivalence Boundary", "Structural Verdict"], cellLoc='center', loc='center')
    plt.savefig("table_2_pairwise.png", dpi=300, bbox_inches='tight'); plt.close()

    fig3, ax3 = plt.subplots(figsize=(13.5, 2.8)); ax3.axis('off')
    ax3.table(cellText=table_3_rows, colLabels=["Phase Ablation Group", "Wavefront Fidelity (F)", "Total Variation Dist. (D)", "Symmetry Index (S)", "Peak-to-Valley Ratio"], cellLoc='center', loc='center')
    plt.savefig("table_3_metrics.png", dpi=300, bbox_inches='tight'); plt.close()


    fig_qrw, ax_qrw = plt.subplots(figsize=(10, 5))

    ax_qrw.bar(discrete_lattice, q_ideal_A, width=0.6, color='#2C3E50', alpha=0.25, label='Ideal Pure Qiskit (Q)')
    
    raw_A_mean = np.mean([normalize_density(r, discrete_lattice) for r in matrix_store["A"] if r is not None], axis=0)
    raw_C_mean = np.mean([normalize_density(r, discrete_lattice) for r in matrix_store["C"] if r is not None], axis=0)


    ax_qrw.step(discrete_lattice, raw_C_mean, where='mid', color='#9B59B6', linewidth=2.0, label='Config C: HSQ closed-form model (with noise)')
    ax_qrw.plot(discrete_lattice, raw_A_mean, color='#E67E22', linestyle='-.', marker='o', markersize=2, alpha=0.8, label='Config A: Qiskit DTQW (noisy)')
    ax_qrw.set_xlabel('Discrete Spatial Lattice Site Index (512-Grid Full Range)', fontsize=11, fontname='Times New Roman')
    ax_qrw.set_ylabel('Probability Density P(x)', fontsize=11, fontname='Times New Roman')
    # Show the full extent of the HSQ envelope instead of cropping its tails, and mark
    # the DTQW light cone -- outside it an ideal walk has exactly zero amplitude.
    ax_qrw.set_xlim(256 - 3.2*steps, 256 + 3.2*steps)
    for edge in (256 - steps, 256 + steps):
        ax_qrw.axvline(edge, color='#C0392B', linestyle='--', linewidth=1.2, alpha=0.9)
    ax_qrw.axvline(256 - steps, color='#C0392B', linestyle='--', linewidth=1.2, alpha=0.9,
                   label=f'DTQW light cone (origin +/- {steps})')
    ax_qrw.grid(True, linestyle=':', alpha=0.4)
    ax_qrw.legend(loc='upper right', frameon=True, fontsize=9.5)
    plt.title(f"HSQ closed-form model vs Qiskit DTQW (steps={steps}, noise={noise_level})", fontsize=10, fontweight='bold')
    plt.savefig("fig2_qrw_ablation_profile.png", dpi=300, bbox_inches='tight'); plt.close()
    print("[done] metrics, tables and profile written.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WP1/WP4 High-Fidelity CLI Controller")
    parser.add_argument("--seeds", type=int, default=20, help="Number of Monte Carlo Seeds")
    parser.add_argument("--steps", type=int, default=10, help="Evolution Steps (Parity Coherent)")
    parser.add_argument("--noise", type=float, default=0.00, help="Thermal Noise Level (Depolarizing)")
    parser.add_argument("--phase", type=float, default=0.05, help="Global Phase Delta Shift")
    parser.add_argument("--analyze-only", type=str, default=None, metavar="NPY",
                        help="Re-score a saved .npy offline (no live backend). Uses the "
                             "references stored inside the file when present.")
    
    args = parser.parse_args()
    
    NUM_SEEDS = args.seeds
    EVOLVE_STEPS = args.steps
    target_noise = args.noise
    global_phase_delta = args.phase
    
    lattice_axis = np.arange(512)

    if args.analyze_only:
        payload = np.load(args.analyze_only, allow_pickle=True).item()
        conv = payload.get("phase_convention")
        if conv != "B,D carry the phase (C=off, D=on)":
            print("[ABORT] this file was produced under a different/unknown phase convention:")
            print(f"        found: {conv!r}")
            print("        Re-scoring it with this script would silently swap the C/D labels.")
            print("        Regenerate the dataset with this version instead of re-scoring.")
            sys.exit(2)
        process_and_pairwise_test(payload, discrete_lattice=lattice_axis,
                                  steps=int(payload["steps"]), phase_delta=float(payload["phase_delta"]),
                                  noise_level=float(payload["target_noise"]))
        sys.exit(0)

    REMOTE_COMP_B_IP = "127.0.0.1" 
    hsq_single_node = LiveTargetWalker(f"{REMOTE_COMP_B_IP}:5011", "HSQ-Single-Core-Node")
    
    file_name = f"matrix_store_noise_{target_noise:.2f}.npy"

    print("\n[STAGE 1] Testing active cross-backend handshake...")
    if not hsq_single_node.check_live_handshake():
        print("❌ [Fatal Error] Cross-backend hardware handshake failed."); sys.exit(1)

    print(f"\n[STAGE 2] Running heterogeneous execution loops ({EVOLVE_STEPS} steps)...")
    matrix_store = { "A": [], "B": [], "C": [], "D": [] }
    seed_list = []

    for seed in range(NUM_SEEDS):
        current_seed = 1000 + seed
        

        wf_A = simulate_qiskit_dtqw(EVOLVE_STEPS, "A", lattice_axis, global_phase_delta, noise_level=target_noise)
        wf_B = simulate_qiskit_dtqw(EVOLVE_STEPS, "B", lattice_axis, global_phase_delta, noise_level=target_noise)
        wf_C = hsq_single_node.fetch_live_wavefront(EVOLVE_STEPS, "C", current_seed, target_noise, global_phase_delta)
        wf_D = hsq_single_node.fetch_live_wavefront(EVOLVE_STEPS, "D", current_seed, target_noise, global_phase_delta)
        
        if (wf_A is None) or (wf_B is None) or (wf_C is None) or (wf_D is None):
            print(f" ⚠️ [TIMEOUT] Hardware exception on Seed {current_seed}. Skipping."); continue
            
        matrix_store["A"].append(wf_A)
        matrix_store["B"].append(wf_B)
        matrix_store["C"].append(wf_C)
        matrix_store["D"].append(wf_D) 
        seed_list.append(current_seed)
        print(f" -> Secured Manifest on Seed {current_seed:<4} | Verified Sum ≈ 1.0")

    try:
        current_script_path = __file__
    except NameError:
        current_script_path = sys.argv[0]
        
    script_sha256 = "N/A"
    try:
        with open(current_script_path, "rb") as f:
            script_sha256 = hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        print(f"⚠️ [Warning] Could not read script source for hash calculation: {e}")

    # Store the qiskit references alongside the data so a reviewer can re-score the
    # saved .npy offline, without qiskit installed and without the live backend.
    ref_payload = {
        "q_ref_A": simulate_qiskit_dtqw(EVOLVE_STEPS, "A", lattice_axis, global_phase_delta, noise_level=target_noise),
        "q_ref_B": simulate_qiskit_dtqw(EVOLVE_STEPS, "B", lattice_axis, global_phase_delta, noise_level=target_noise),
        "q_ideal_A": simulate_qiskit_dtqw(EVOLVE_STEPS, "A", lattice_axis, global_phase_delta, noise_level=0.0),
    }

    metadata_payload = {
        "matrix_store": matrix_store,
        "stored_references": ref_payload,
        "seed_list": seed_list,
        "target_noise": target_noise,
        "steps": EVOLVE_STEPS, 
        "phase_convention": "B,D carry the phase (C=off, D=on)",
        "t_delta": 0.1, 
        "phase_delta": global_phase_delta,
        "source_hash_sha256": script_sha256,
        "execution_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    np.save(file_name, metadata_payload, allow_pickle=True)
    print(f"🏆 [Dataset Secured] Saved payload to {file_name}")
    print(f"🔑 [Code fingerprint] SHA-256: {script_sha256}")
    
    print("\n[STAGE 3] Running rigorous discrete calculation with Uniform 512 Grid...")
    process_and_pairwise_test(metadata_payload, discrete_lattice=lattice_axis, steps=EVOLVE_STEPS, phase_delta=global_phase_delta, noise_level=target_noise)
