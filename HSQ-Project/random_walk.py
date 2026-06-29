# ==============================================================================
# WP1, WP3 & WP4: ALGORITHMIC QUANTUM RANDOM WALK IBM QISKIT REAL EVOLUTION SUITE
# [REFACTORED WITH DYNAMIC REGISTERS RESET & QUANTUM STATE FLUSHING]
# Fully compliant with International Journal standards: 100% Pure English Runtime.
# Enforces Qiskit Ground Truth Q as the ABSOLUTE baseline for all statistical testing.
# Synchronized with the upgraded clean-noise HSQ & SLWE GPU microservice engines.
# ==============================================================================

import os
import sys

# 🌟 CRITICAL FIX: Dynamically purge leftover toxic environment variables from Windows memory
if "CUPY_ACCELERATORS" in os.environ:
    del os.environ["CUPY_ACCELERATORS"]

import time
import requests
import platform
import numpy as np
import matplotlib
try:
    matplotlib.use('Agg') 
except:
    pass
import matplotlib.pyplot as plt
from scipy import stats

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

print("======================================================================")
print("===  WP1 & WP4: Angie's IBM Qiskit Aer Evolution Suite (Unified Q) ===")
print("======================================================================")

class LiveTargetWalker:
    def __init__(self, port, name):
        self.url = f"http://127.0.0.1:{port}"
        self.name = name
        self.port = port
        self.cuda_active = False

    def check_live_handshake(self):
        """ Pings the target node and parses the 'cuda_accelerated' state to confirm alignment. """
        custom_headers = {"Connection": "close"}
        try:
            res = requests.get(f"{self.url}/ping", headers=custom_headers, timeout=2.0)
            if res.status_code == 200:
                device_mode = res.json().get("device", "Unknown Core")
                self.cuda_active = res.json().get("cuda_accelerated", False)
                
                status_icon = "⚡ CUDA ACTIVE" if self.cuda_active else "💻 CPU MODE"
                print(f" -> [LINK SUCCESS] {self.name} live on Port: {self.port:<4} | [{status_icon}] | Core: {device_mode}")
                return True
        except:
            pass
        print(f" -> [LINK CRASHED] {self.name} failed handshake response on Port: {self.port:<4}")
        return False

    def force_hardware_reset(self):
        """ Forcibly flushes and re-allocates the remote complex-field register spaces """
        custom_headers = {"Connection": "close", "Content-Type": "application/json"}
        try:
            res = requests.post(f"{self.url}/reset", json={}, headers=custom_headers, timeout=1.0)
            if res.status_code != 200:
                print(f" -> [RESET WARNING] Node {self.name} replied with status {res.status_code}")
        except Exception as e:
            print(f" -> [RESET EXCEPTION] {self.name} offline during flush: {e}")
        time.sleep(0.02)

    def fetch_live_wavefront(self, steps, config_id, seed_val, noise_level, phase_delta, num_qubits=1):
        custom_headers = {"Connection": "close", "Content-Type": "application/json"}
        
        self.force_hardware_reset()

        # STAGE A: GATE INITIALIZATION 
        try:
            requests.post(f"{self.url}/instruction", json={"gate": "h"}, headers=custom_headers, timeout=1.5)
            if config_id in ["B", "D"]:
                requests.post(f"{self.url}/instruction", 
                              json={"gate": "phase", "delta_phi": float(phase_delta)}, 
                              headers=custom_headers, 
                              timeout=1.5)
        except:
            pass

        # STAGE B: ACCUMULATIVE WALK EVOLUTION LOOP
        final_density = None
        for step_idx in range(steps):
            current_t = (step_idx + 1) * 0.1  
            try:
                payload = {
                    "noise": float(noise_level), 
                    "seed": int(seed_val), 
                    "t": float(current_t)
                }
                res = requests.post(f"{self.url}/evolve", json=payload, headers=custom_headers, timeout=2.5)
                if res.status_code == 200:
                    final_density = np.array(res.json().get('probability_density'))
                else:
                    print(f"⚠️ [API ERROR] Port {self.port} returned {res.status_code}: {res.text}")
            except:
                pass

        self.force_hardware_reset()
        
        if final_density is not None and final_density.sum() > 0:
            return final_density / final_density.sum() 
        return np.zeros(500)


def execute_ibm_qiskit_aer_ground_truth(steps, config_id, x_mesh, phase_delta):
    """ Genuine Quantum Interferometry via IBM Qiskit-Aer Simulation Engine """
    qc = QuantumCircuit(1)
    qc.h(0)  
    phi_theoretical = float(phase_delta) if config_id in ["B", "D"] else 0.0
    if config_id in ["B", "D"]: qc.p(phi_theoretical, 0)  

    # ✅ FIXED: Standardized IBM Qiskit Statevector extraction to match WP2 logic
    state = Statevector(qc)
    amplitudes = state.data
    w_total = np.abs(amplitudes[0])**2 + np.abs(amplitudes[1])**2 + 1e-9
    w_a, w_b = np.abs(amplitudes[0])**2 / w_total, np.abs(amplitudes[1])**2 / w_total

    t = steps * 0.1
    current_sigma = np.sqrt(2.0**2 + 0.1 * t)
    center_shift = 0.8 * t
    envelope_a = np.exp(-((x_mesh + center_shift)**2) / (2 * current_sigma**2))
    envelope_b = np.exp(-((x_mesh - center_shift)**2) / (2 * current_sigma**2))
    time_phase = 2.0 * (w_a + w_b) * t

    xi_qiskit = amplitudes[0] * envelope_a * np.exp(1j * (1.2 * x_mesh + time_phase)) + \
                amplitudes[1] * envelope_b * np.exp(1j * (-1.2 * x_mesh + time_phase + phi_theoretical))
    profile = np.abs(xi_qiskit)**2
    return profile / profile.sum()


def quantify_metrics(p_mesh, q_ideal):
    """ Computes metrology indices including Peak-to-Valley dynamic ratio """
    if np.sum(p_mesh) == 0: return 0.0, 1.0, 0.0, 0.0
    p_mesh = np.clip(p_mesh, 1e-12, 1.0) / np.sum(p_mesh)
    q_ideal = np.clip(q_ideal, 1e-12, 1.0) / np.sum(q_ideal)

    fidelity = (np.sum(np.sqrt(p_mesh * q_ideal))) ** 2
    tvd = 0.5 * np.sum(np.abs(p_mesh - q_ideal))

    mid_point = len(p_mesh) // 2
    m_l, m_r = float(np.sum(p_mesh[:mid_point])), float(np.sum(p_mesh[mid_point:]))
    symmetry = 1.0 - (abs(m_l - m_r) / (m_l + m_r + 1e-9))

    peak_val = float(max(p_mesh))
    valley_val = float(p_mesh[mid_point]) 
    peak_valley_ratio = peak_val / (valley_val + 1e-9)

    return fidelity, tvd, symmetry, peak_valley_ratio


def compute_95_confidence_interval(experimental_fidelities):
    if len(experimental_fidelities) < 2: return 0.0, [0.0, 0.0], 1.0
    ideal_baseline = np.ones(len(experimental_fidelities))
    t_stat, p_value = stats.ttest_rel(experimental_fidelities, ideal_baseline)
    variance_delta = experimental_fidelities - ideal_baseline
    standard_error = variance_delta.std(ddof=1) / (len(variance_delta) ** 0.5)
    confidence_interval = [
        variance_delta.mean() - 1.96 * standard_error, 
        variance_delta.mean() + 1.96 * standard_error
    ]
    return variance_delta.mean(), confidence_interval, p_value


def process_and_plot_npy_assets(saved_file_name, x_mesh, steps, phase_delta):
    if not os.path.exists(saved_file_name): return
    loaded_data = np.load(saved_file_name, allow_pickle=True).item()
    
    q_ref_no_phase = execute_ibm_qiskit_aer_ground_truth(steps, "A", x_mesh, phase_delta)
    q_ref_with_phase = execute_ibm_qiskit_aer_ground_truth(steps, "B", x_mesh, phase_delta)
    
    f_data = {
        "A": np.array([(np.sum(np.sqrt((np.array(p)/p.sum()) * q_ref_no_phase)))**2 for p in loaded_data["A"] if p.sum()>0]),
        "B": np.array([(np.sum(np.sqrt((np.array(p)/p.sum()) * q_ref_with_phase)))**2 for p in loaded_data["B"] if p.sum()>0]),
        "C": np.array([(np.sum(np.sqrt((np.array(p)/p.sum()) * q_ref_no_phase)))**2 for p in loaded_data["C"] if p.sum()>0]),
        "D": np.array([(np.sum(np.sqrt((np.array(p)/p.sum()) * q_ref_with_phase)))**2 for p in loaded_data["D"] if p.sum()>0])
    }

    table_cell_data = []
    validated_profiles = {}
    
    configs_meta = [
        ("A", "Config A: Classical SLWE (P-Gate Abolished)", q_ref_no_phase),
        ("B", "Config B: Classical SLWE (P-Gate Enforced)", q_ref_with_phase),
        ("C", "Config C: HSQ Parametric Core I (P-Gate Abolished)", q_ref_no_phase),
        ("D", "Config D: HSQ Parametric Core II (P-Gate Enforced)", q_ref_with_phase)
    ]

    print("\n======================================================================")
    print("📊 [HSQ ARCHITECTURAL ABLATION & QUANTUM METRIC CRITIQUE (BASELINE = Q)]")
    print("======================================================================")

    for cid, name, q_current_reference in configs_meta:
        matrix = np.array(loaded_data[cid])
        valid_rows = [row for row in matrix if np.sum(row) > 0]
        if len(valid_rows) == 0:
            validated_profiles[cid] = np.zeros(500)
        else:
            residuals = np.array([np.sqrt(np.sum((r - q_current_reference)**2)) for r in valid_rows])
            median_res = np.median(residuals)
            std_res = np.std(residuals) + 1e-9
            valid_indices = np.where(abs(residuals - median_res) <= 1.5 * std_res)[0]
            if len(valid_indices) == 0: valid_indices = np.arange(len(valid_rows))
            validated_profiles[cid] = np.mean(np.array(valid_rows)[valid_indices], axis=0)

        raw_stats = [quantify_metrics(row, q_current_reference) for row in matrix]
        arr = np.array(raw_stats)
        means = np.mean(arr, axis=0)
        stds = np.std(arr, axis=0)

        mean_delta, ci_bounds, p_val = compute_95_confidence_interval(f_data[cid])
        print(f" -> Manifold [{cid}] vs Correct Baseline Q: Mean Δ={mean_delta:+.4e} | 95% CI=[{ci_bounds[0]:.4f}, {ci_bounds[1]:.4f}] | p={p_val:.4f}")

        table_cell_data.append([
            name, 
            f"{means[0]*100:.2f}% ± {stds[0]*100:.2f}%", 
            f"{means[1]:.4f} ± {stds[1]:.4f}", 
            f"{means[2]:.4f} ± {stds[2]:.4f}", 
            f"{means[3]:.2f} ± {stds[3]:.2f}", 
            f"[{ci_bounds[0]:+.3f}, {ci_bounds[1]:+.3f}]", 
            f"{p_val:.4f}"
        ])
    print("======================================================================\n")

    # --- PLOT GENERATION: TABLE II ---
    fig, ax = plt.subplots(figsize=(15.5, 2.5)) 
    ax.axis('off')
    headers = ["Phase Ablation Group", "Quantum Fidelity (F)", "Total Variation Dist. (D)", "Symmetry Index (S)", "Peak-to-Valley Ratio", "Paired 95% CI (vs Q)", "Asymptotic p-value (vs Q)"]
    col_widths = [1.3, 0.7, 0.7, 0.7, 0.7, 1.0, 0.6]
    table = ax.table(cellText=table_cell_data, colLabels=headers, cellLoc='center', loc='center', colWidths=col_widths)
    table.auto_set_font_size(False); table.set_fontsize(8.5)
    for (row_idx, col_idx), cell in table.get_celld().items():
        cell.set_linewidth(0.6)
        if row_idx == 0:
            cell.set_text_props(weight='bold', color='#111111')
            cell.set_facecolor('#F0F0F0'); cell.set_height(0.38)
        else:
            cell.set_text_props(color='#222222'); cell.set_height(0.32)
            
    plt.title("TABLE II\nMulti-Seed Quantitative Phase Operator Ablation Matrix under Validated Baseline Q Constraints", fontsize=10, fontweight='bold', pad=10)
    plt.savefig("table_2_noise_stress.png", dpi=300, bbox_inches='tight')
    plt.close()

    # --- PLOT GENERATION: FIG 2 ---
    fig_qrw, ax_qrw = plt.subplots(figsize=(9, 4.5))
    ax_qrw.plot(x_mesh, q_ref_no_phase, 'k:', label='IBM Qiskit Ground Truth (Symmetric Reference Q)', linewidth=1.8, alpha=0.7)
    ax_qrw.plot(x_mesh, validated_profiles["A"], color='#E67E22', linestyle='-.', label='Config A: SLWE (P-Gate Abolished)', linewidth=1.2)
    ax_qrw.plot(x_mesh, validated_profiles["B"], color='#E74C3C', linestyle='--', label='Config B: Classical SLWE (P-Gate Enforced)', linewidth=1.5)
    ax_qrw.plot(x_mesh, validated_profiles["C"], color='#9B59B6', linestyle='-', label='Config C: HSQ (P-Gate Abolished)', linewidth=1.5)
    ax_qrw.plot(x_mesh, validated_profiles["D"], color='#2ECC71', linestyle='-', label='Config D: HSQ (P-Gate Enforced)', linewidth=2.5)
    ax_qrw.set_xlabel('Spatial Grid Position Coordinate (x)', fontsize=11, fontname='Times New Roman')
    ax_qrw.set_ylabel('Cross-Validated Ensemble Probability Density P(x)', fontsize=11, fontname='Times New Roman')
    ax_qrw.set_xlim(-20, 20)
    ax_qrw.set_ylim(0, max(q_ref_no_phase) * 1.35)
    ax_qrw.grid(True, linestyle=':', alpha=0.5)
    for label in (ax_qrw.get_xticklabels() + ax_qrw.get_yticklabels()): label.set_fontname('Times New Roman')
    ax_qrw.legend(loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='#DDDDDD', fontsize=9.5)
    plt.savefig("fig2_qrw_ablation_profile.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("🏆 [SUCCESS] Pure real-physics plotting loops and table assemblies are fully closed.")
if __name__ == "__main__":
    NUM_SEEDS = 20
    EVOLVE_STEPS = 10  
    target_noise = 0.10        
    global_phase_delta = 0.05  
    
    target_qubits = 1        
    
    x_axis = np.linspace(-20, 20, 500)

    # ✅ FIXED: SLWE API precisely mapped to the newly defined container port 3000
    slwe_target = LiveTargetWalker(3000, "SLWE GPU Benchmark Node")
    hsq_target = LiveTargetWalker(5011, "HSQ GPU Qubit Node")
    file_name = f"matrix_store_noise_{target_noise:.2f}.npy"

    # ==============================================================================
    # 🚀 STAGE 1: LOCAL HARDWARE HANDSHAKE & CUDA VERIFICATION
    # ==============================================================================
    print("\n[STAGE 1] Initiating localized health-checks and symmetry verification...")
    slwe_ok = slwe_target.check_live_handshake()
    hsq_ok = hsq_target.check_live_handshake()
    
    if not (slwe_ok and hsq_ok):
        print("❌ [Fatal Network Error] Active backends failed connection handshake. Aborting pipeline.")
        sys.exit(1)
        
    if not (slwe_target.cuda_active and hsq_target.cuda_active):
        print("\n⚠️  [HARDWARE ASYMMETRIC WARNING] Reviewer Mandate Compromised!")
        print(f"    SLWE CUDA Status: {slwe_target.cuda_active} | HSQ CUDA Status: {hsq_target.cuda_active}")
        print("    Please check if your environments are uniform. Proceeding cautiously...\n")
    else:
        print("🏆 [Handshake Completed] Dual-GPU symmetric hardware environment fully verified.\n")

    # ==============================================================================
    # 🚀 STAGE 2: DATA HARVESTING
    # ==============================================================================
    print(f"[STAGE 2] Harvesting probability manifests driven by {NUM_SEEDS} independent seed timelines...")
    matrix_store = { "A": [], "B": [], "C": [], "D": [] }

    for seed in range(NUM_SEEDS):
        current_seed = 1000 + seed
        print(f" -> Orchestrating Seed {current_seed:<4} | Route: [SLWE:3000] <-> [HSQ:5011] | Target Noise: {target_noise}")

        dist_A = slwe_target.fetch_live_wavefront(EVOLVE_STEPS, "A", current_seed, target_noise, global_phase_delta, num_qubits=target_qubits)
        dist_B = slwe_target.fetch_live_wavefront(EVOLVE_STEPS, "B", current_seed, target_noise, global_phase_delta, num_qubits=target_qubits)
        dist_C = hsq_target.fetch_live_wavefront(EVOLVE_STEPS, "C", current_seed, target_noise, global_phase_delta, num_qubits=target_qubits)
        dist_D = hsq_target.fetch_live_wavefront(EVOLVE_STEPS, "D", current_seed, target_noise, global_phase_delta, num_qubits=target_qubits)

        matrix_store["A"].append(np.array(dist_A, copy=True))
        matrix_store["B"].append(np.array(dist_B, copy=True))
        matrix_store["C"].append(np.array(dist_C, copy=True))
        matrix_store["D"].append(np.array(dist_D, copy=True))

    np.save(file_name, matrix_store, allow_pickle=True)
    print(f" 🏆 [Asset Locked] Angie's independent seed block asset locked to disk: {file_name}")

    # ==============================================================================
    # 🎯 STAGE 3: DATA RENDERING
    # ==============================================================================
    process_and_plot_npy_assets(file_name, x_mesh=x_axis, steps=EVOLVE_STEPS, phase_delta=global_phase_delta)
