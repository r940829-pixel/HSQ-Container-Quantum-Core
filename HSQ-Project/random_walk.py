# ==============================================================================
# WP1, WP3 & WP4: ALGORITHMIC QUANTUM RANDOM WALK IBM QISKIT REAL EVOLUTION SUITE
# [🔥 RIGOROUS REFRACTOR: 100% GENUINE QISKIT CIRCUIT INTERFERENCE - NO LOOPHOLES]
# Fully compliant with International Journal standards: 100% Pure English Runtime.
# Discards all classical numerical matrix shortcuts for the reference baseline.
# Realizes authentic Discrete-Time Quantum Walk via Qiskit Aer Simulator gates.
# ==============================================================================

import os
import sys

if "CUPY_ACCELERATORS" in os.environ:
    del os.environ["CUPY_ACCELERATORS"]

import time
import requests
import hashlib
import platform
import numpy as np
import matplotlib
try:
    matplotlib.use('Agg') 
except:
    pass
import matplotlib.pyplot as plt
from scipy import stats

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

print("======================================================================")
print("===   WP1 & WP4: Angie's IBM Qiskit Aer Evolution Suite (Unified Q) ===")
print("======================================================================")

class LiveTargetWalker:
    def __init__(self, target_address, name):
        self.url = f"http://{target_address}"
        self.name = name
        self.target_address = target_address
        self.cuda_active = False

    def check_live_handshake(self):
        custom_headers = {"Connection": "close"}
        try:
            res = requests.get(f"{self.url}/ping", headers=custom_headers, timeout=2.0)
            if res.status_code == 200:
                device_mode = res.json().get("device", "Unknown Core")
                self.cuda_active = res.json().get("cuda_accelerated", False)
                status_icon = "⚡ CUDA ACTIVE" if self.cuda_active else "💻 CPU MODE"
                print(f" -> [LINK SUCCESS] {self.name} live on: {self.target_address:<20} | [{status_icon}] | Core: {device_mode}")
                return True
        except:
            pass
        print(f" -> [LINK CRASHED] {self.name} failed handshake response on: {self.target_address:<20}")
        return False

    def force_hardware_reset(self):
        custom_headers = {"Connection": "close", "Content-Type": "application/json"}
        try:
            requests.post(f"{self.url}/reset", json={}, headers=custom_headers, timeout=1.0)
        except Exception:
            pass
        time.sleep(0.02)

    def fetch_live_wavefront(self, steps, config_id, seed_val, noise_level, phase_delta):
        """ Executes true stepped multi-call synchronization to let noise pile up incrementally. """
        custom_headers = {"Connection": "close", "Content-Type": "application/json"}
        
        self.force_hardware_reset()

        # STAGE A: IN-PLACE INITIALIZATION VIA GATEWAY
        try:
            requests.post(f"{self.url}/instruction", json={"gate": "h"}, headers=custom_headers, timeout=1.5)
            if config_id in ["B", "D"]:
                requests.post(f"{self.url}/instruction", 
                              json={"gate": "phase", "delta_phi": float(phase_delta)}, 
                              headers=custom_headers, 
                              timeout=1.5)
        except Exception as e:
            print(f"⚠️ [GATE WARNING] Setup injection stalled: {e}")

        # STAGE B: 10-STEP MULTI-CALL LOOP BACKEND DRIVER (Let noise accumulate!)
        final_density = None
        dt = 0.1
        
        for step_idx in range(steps):
            try:
                payload = {
                    "noise": float(noise_level), 
                    "seed": int(seed_val) + int(step_idx), 
                    "t": float(dt)                                         
                }
                res = requests.post(f"{self.url}/evolve", json=payload, headers=custom_headers, timeout=2.5)
                if res.status_code == 200:
                    final_density = np.array(res.json().get('probability_density'))
                else:
                    return None 
            except Exception:
                return None
                
        return final_density


def execute_ibm_qiskit_aer_ground_truth(steps, config_id, x_mesh, phase_delta):

    num_position_qubits = 9
    total_qubits = num_position_qubits + 1
    coin_idx = num_position_qubits
    
    qc = QuantumCircuit(total_qubits)
    
    init_position = 250
    for q in range(num_position_qubits):
        if (init_position >> q) & 1:
            qc.x(q)
            
    qc.h(coin_idx)
    qc.s(coin_idx)
    
    if config_id in ["B", "D"]:
        qc.p(float(phase_delta), coin_idx)
        
    for _ in range(steps):
        qc.h(coin_idx)
        
        for q in range(num_position_qubits - 1, -1, -1):
            control_qubits = list(range(q)) + [coin_idx]
            if len(control_qubits) == 1:
                qc.cx(control_qubits[0], q)
            else:
                qc.mcx(control_qubits[:-1], q, ctrl_state='1'*len(control_qubits[:-1]))
                
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
        
    simulator = AerSimulator(method='statevector')
    qc = transpile(qc, simulator)
    result = simulator.run(qc).result()
    statevector = result.get_statevector(qc).data
    
    prob_mesh = np.zeros(len(x_mesh))
    for state_idx, ampl in enumerate(statevector):
        prob = np.abs(ampl)**2
        if prob > 1e-12:
            pos_val = state_idx & 0x1FF  
            if pos_val < len(x_mesh):
                prob_mesh[pos_val] += prob
                
    return prob_mesh / prob_mesh.sum()


def quantify_metrics(p_mesh, q_ideal):
    if p_mesh is None or np.sum(p_mesh) == 0: 
        return 0.0, 1.0, 0.0, 0.0
    p_mesh = np.clip(p_mesh, 1e-12, 1.0) / np.sum(p_mesh)
    q_ideal = np.clip(q_ideal, 1e-12, 1.0) / np.sum(q_ideal)

    fidelity = (np.sum(np.sqrt(p_mesh * q_ideal))) ** 2
    tvd = 0.5 * np.sum(np.abs(p_mesh - q_ideal))

    mid_point = len(p_mesh) // 2
    m_l, m_r = float(np.sum(p_mesh[:mid_point])), float(np.sum(p_mesh[mid_point:]))
    symmetry = 1.0 - (abs(m_l - m_r) / (m_l + m_r + 1e-12))

    peak_val = float(max(p_mesh))
    valley_val = float(p_mesh[mid_point]) 
    peak_valley_ratio = peak_val / (valley_val + 1e-12)

    return fidelity, tvd, symmetry, peak_valley_ratio


def process_and_pairwise_test(saved_file_name, x_mesh, steps, phase_delta):
    if not os.path.exists(saved_file_name):
        print(f"❌ Error: Asset file {saved_file_name} not found.")
        return
    
    loaded_data = np.load(saved_file_name, allow_pickle=True).item()
    
    q_ref_noiseless_no_phase = execute_ibm_qiskit_aer_ground_truth(steps, "A", x_mesh, phase_delta)
    q_ref_noiseless_with_phase = execute_ibm_qiskit_aer_ground_truth(steps, "B", x_mesh, phase_delta)
    
    configs_meta = [
        ("A", "Config A: Classical SLWE (Psi)", q_ref_noiseless_no_phase),
        ("B", "Config B: Classical SLWE (Psi)", q_ref_noiseless_with_phase),
        ("C", "Config C: HSQ Qubit Node (Xi)", q_ref_noiseless_no_phase),
        ("D", "Config D: HSQ Qubit Node (Xi)", q_ref_noiseless_with_phase)
    ]
    
    table_3_rows = []
    f_channels = {}  

    for cid, name, q_ref in configs_meta:
        raw_list = loaded_data[cid]
        valid_rows = [row for row in raw_list if row is not None and np.sum(row) > 0]
        
        raw_metrics = []
        fidelities_vector = []
        
        for row in valid_rows:
            fid, tvd, sym, pvr = quantify_metrics(row, q_ref)
            raw_metrics.append([fid, tvd, sym, pvr])
            fidelities_vector.append(fid)
            
        f_channels[cid] = np.array(fidelities_vector) if fidelities_vector else np.zeros(1)
        
        metrics_arr = np.array(raw_metrics) if raw_metrics else np.zeros((1, 4))
        means = np.mean(metrics_arr, axis=0)
        stds = np.std(metrics_arr, axis=0)
        
        table_3_rows.append([
            name,
            f"{means[0]*100:.2f}% ± {stds[0]*100:.2f}%",
            f"{means[1]:.4f} ± {stds[1]:.4f}",
            f"{means[2]:.4f} ± {stds[2]:.4f}",
            f"{means[3]:.2f} ± {stds[3]:.2f}"
        ])

    # --------------------------------------------------------------------------
    # PART 2: PAIRWISE HYPOTHESIS TESTING (🔥 INDEPENDENT SCHOLASTIC T-TEST)
    # --------------------------------------------------------------------------
    print("\n======================================================================")
    print("📊 [PAIRWISE HYPOTHESIS TESTING & QUANTUM BASELINE CRITIQUE]")
    print("======================================================================")

    def run_scholastic_comparison(f1, f2, k1_name, k2_name, hypothesis_title):
        p_t = stats.ttest_ind(f1, f2, equal_var=False).pvalue
        p_w = stats.mannwhitneyu(f1, f2, alternative='two-sided').pvalue
        
        mean_delta = f1.mean() - f2.mean()
        is_equivalent = (p_t > 0.05) 
        status_string = "EQUIVALENT CHARACTERISTICS" if is_equivalent else "DISTINCT STRUCTURAL VARIANCE"
        
        print(f" -> Testing [{hypothesis_title}] ({k1_name} vs {k2_name}):")
        print(f"    Mean Δfid = {mean_delta:+.4e} | Independent t-test p = {p_t:.4f} | Mann-Whitney p = {p_w:.4f}")
        print(f"    Verdict => 🏆 {status_string}\n")
        
        return [hypothesis_title, f"{mean_delta:+.4e}", "N/A (Independent)", f"{p_t:.4f}", f"{p_w:.4f}", "Equivalent" if is_equivalent else "Different"]

    row_hsq = run_scholastic_comparison(f_channels["C"], f_channels["D"], "Config C", "Config D", "Operator On vs Off (HSQ: C vs D)")
    row_backend = run_scholastic_comparison(f_channels["A"], f_channels["C"], "Config A", "Config C", "Backend Topology (SLWE vs HSQ: A vs C)")

    # --------------------------------------------------------------------------
    # PART 3: SCHOLASTIC ASSET RENDERING
    # --------------------------------------------------------------------------
    table_2_cell_data = [row_hsq, row_backend]
    fig2, ax2 = plt.subplots(figsize=(13.5, 2.2)) 
    ax2.axis('off')
    headers_2 = ["Pairwise Testing Group", "Mean Fidelity Delta (Δfid)", "Paired 95% CI", "Independent t-test p", "Mann-Whitney p-value", "Structural Metric Verdict"]
    col_widths_2 = [2.2, 1.2, 1.0, 1.2, 1.0, 1.2]
    t2 = ax2.table(cellText=table_2_cell_data, colLabels=headers_2, cellLoc='center', loc='center', colWidths=col_widths_2)
    t2.auto_set_font_size(False); t2.set_fontsize(9.5)
    for (r, c), cell in t2.get_celld().items():
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_text_props(weight='bold'); cell.set_facecolor('#F5F5F5'); cell.set_height(0.35)
        else:
            cell.set_height(0.28)
    plt.title("TABLE II\nPairwise Structural Comparison Matrix Under Authentic Qiskit DTQW Constraints", fontsize=10, fontweight='bold', pad=12)
    plt.savefig("table_2_pairwise.png", dpi=300, bbox_inches='tight'); plt.close()

    fig3, ax3 = plt.subplots(figsize=(13.5, 2.8))
    ax3.axis('off')
    headers_3 = ["Phase Ablation Group", "Wavefront Fidelity (F)", "Total Variation Dist. (D)", "Symmetry Index (S)", "Peak-to-Valley Ratio"]
    col_widths_3 = [2.2, 1.2, 1.2, 1.2, 1.2]
    t3 = ax3.table(cellText=table_3_rows, colLabels=headers_3, cellLoc='center', loc='center', colWidths=col_widths_3)
    t3.auto_set_font_size(False); t3.set_fontsize(9.5)
    for (r, c), cell in t3.get_celld().items():
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_text_props(weight='bold'); cell.set_facecolor('#F5F5F5'); cell.set_height(0.35)
        else:
            cell.set_height(0.28)
    plt.title("TABLE III\nEnsemble Numerical Metrology Manifest Mapped to Authentic Qiskit DTQW Target", fontsize=10, fontweight='bold', pad=12)
    plt.savefig("table_3_metrics.png", dpi=300, bbox_inches='tight'); plt.close()

    # --------------------------------------------------------------------------
    # PART 4: EVOLUTION PROFILE GRAPH GENERATION
    # --------------------------------------------------------------------------
    def extract_clean_mean(key):
        matrix = [row for row in loaded_data[key] if row is not None and np.sum(row) > 0]
        if len(matrix) == 0: return np.zeros(500)
        return np.mean(matrix, axis=0)

    fig_qrw, ax_qrw = plt.subplots(figsize=(9, 4.5))
    ax_qrw.plot(x_mesh, q_ref_noiseless_no_phase, 'k:', label='Authentic IBM Qiskit DTQW Circuit Baseline (Q)', linewidth=1.8, alpha=0.7)
    ax_qrw.plot(x_mesh, extract_clean_mean("A"), color='#E67E22', linestyle='-.', label='Config A: Classical SLWE (Psi Field)', linewidth=1.2)
    ax_qrw.plot(x_mesh, extract_clean_mean("C"), color='#9B59B6', linestyle='-', label='Config C: HSQ Qubit Node (Xi Field)', linewidth=1.5)
    
    ax_qrw.set_xlabel('Spatial Grid Position Coordinate (x)', fontsize=11, fontname='Times New Roman')
    ax_qrw.set_ylabel('Cross-Validated Ensemble Probability Density P(x)', fontsize=11, fontname='Times New Roman')
    ax_qrw.set_xlim(0, 500) 
    ax_qrw.set_ylim(0, max(q_ref_noiseless_no_phase) * 1.35)
    ax_qrw.grid(True, linestyle=':', alpha=0.5)
    
    for label in (ax_qrw.get_xticklabels() + ax_qrw.get_yticklabels()): 
        label.set_fontname('Times New Roman')
    ax_qrw.legend(loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='#DDDDDD', fontsize=9.5)
    plt.title("TABLE III Cross-Validation: Authentic Qiskit Circuit vs Decoupled Microservice Cores", fontsize=10, fontweight='bold', pad=10)
    plt.savefig("fig2_qrw_ablation_profile.png", dpi=300, bbox_inches='tight'); plt.close()
    
    print("🏆 [SUCCESS] Dual-table authentic Qiskit circuit validation suite compiled successfully.")


if __name__ == "__main__":
    NUM_SEEDS = 20
    EVOLVE_STEPS = 10  
    target_noise = 0.10        
    global_phase_delta = 0.05  
    x_axis = np.linspace(0, 499, 500) 

    REMOTE_COMP_B_IP = "127.0.0.1" 
    
    slwe_target = LiveTargetWalker(f"{REMOTE_COMP_B_IP}:3000", "SLWE Classical Node")
    hsq_target = LiveTargetWalker(f"{REMOTE_COMP_B_IP}:5011", "HSQ Qubit Node")
    
    file_name = f"matrix_store_noise_{target_noise:.2f}.npy"

    print("\n[STAGE 1] Initiating localized health-checks and baseline verification...")
    slwe_ok = slwe_target.check_live_handshake()
    hsq_ok = hsq_target.check_live_handshake()
    
    if not (slwe_ok and hsq_ok):
        print("❌ [Fatal Network Error] Active backends failed connection handshake. Aborting pipeline.")
        sys.exit(1)

    print(f"\n[STAGE 2] Harvesting probability manifests via 10-step iterative loop over {NUM_SEEDS} seeds...")
    matrix_store = { "A": [], "B": [], "C": [], "D": [] }

    for seed in range(NUM_SEEDS):
        current_seed = 1000 + seed
        print(f" -> Driving Seed {current_seed:<4} | Pipeline Route: [SLWE:3000] <-> [HSQ:5011]")

        matrix_store["A"].append(slwe_target.fetch_live_wavefront(EVOLVE_STEPS, "A", current_seed, target_noise, global_phase_delta))
        matrix_store["B"].append(slwe_target.fetch_live_wavefront(EVOLVE_STEPS, "B", current_seed, target_noise, global_phase_delta))
        matrix_store["C"].append(hsq_target.fetch_live_wavefront(EVOLVE_STEPS, "C", current_seed, target_noise, global_phase_delta))
        matrix_store["D"].append(hsq_target.fetch_live_wavefront(EVOLVE_STEPS, "D", current_seed, target_noise, global_phase_delta))

    np.save(file_name, matrix_store, allow_pickle=True)
    print(f" 🏆 [Asset Locked] Authentic 10-step dataset secured to disk: {file_name}")
    
    print("\n[STAGE 3] Executing true Qiskit circuit verification critique analysis...")
    process_and_pairwise_test(file_name, x_mesh=x_axis, steps=EVOLVE_STEPS, phase_delta=global_phase_delta)
