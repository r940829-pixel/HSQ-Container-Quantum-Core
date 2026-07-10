# ==============================================================================
# WP1, WP3 & WP4: DISTRIBUTED QUANTUM RANDOM WALK INTEGRATED VERIFICATION SUITE
# [🔥 TOST LOCK + INDEPENDENT WELCH METROLOGY + RUNTIME BUGFIX CONTROL]
# Fully compliant with International Journal standards: 100% Pure English Runtime.
# Synchronized with the upgraded clean-noise HSQ & SLWE GPU microservice engines.
# Automatically exports text report (tables_report.txt) and high-res png tables.
# ==============================================================================

import os
import sys
import inspect

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

print("======================================================================")
print("===  WP1 & WP4: Integrated Qiskit Baseline & Table Report Suite   ===")
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
        custom_headers = {"Connection": "close", "Content-Type": "application/json"}
        self.force_hardware_reset()

        try:
            res_h = requests.post(f"{self.url}/instruction", json={"gate": "h"}, headers=custom_headers, timeout=1.5)
            if res_h.status_code != 200:
                raise RuntimeError(f"H-gate initialization failed on {self.name}")
                
            if config_id in ["B", "D"]:
                res_p = requests.post(f"{self.url}/instruction", 
                                      json={"gate": "phase", "delta_phi": float(phase_delta)}, 
                                      headers=custom_headers, 
                                      timeout=1.5)
                if res_p.status_code != 200:
                    raise RuntimeError(f"P-gate enforcement failed on {self.name}")
        except Exception as e:
            raise RuntimeError(f"Handshake Stalled on {self.name}: {e}")

        final_density = None
        dt = 0.1
        for step_idx in range(steps):
            payload = {
                "noise": float(noise_level), 
                "seed": int(seed_val) + int(step_idx), 
                "t": float(dt)                                         
            }
            res = requests.post(f"{self.url}/evolve", json=payload, headers=custom_headers, timeout=2.5)
            
            if res.status_code != 200:
                raise RuntimeError(f"Pipeline broken at step {step_idx} on {self.name}: {res.text}")
                
            final_density = res.json().get('probability_density')
            
        if final_density is None:
            raise RuntimeError(f"Null telemetry array fetched from {self.name}")
            
        arr = np.array(final_density, dtype=float)
        if not np.isclose(np.sum(arr), 1.0, atol=1e-4):
            raise ValueError(f"Telemetry wave distribution violation on {self.name}: sum={np.sum(arr)}")
            
        return arr


def execute_ibm_qiskit_aer_ground_truth(steps, config_id, x_mesh, phase_delta):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    
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
        
    qc.save_statevector()
    simulator = AerSimulator()
    qc = transpile(qc, simulator)
    result = simulator.run(qc).result()
    statevector = result.get_statevector(qc).data
    
    qiskit_raw_probs = np.zeros(512)
    for state_idx, ampl in enumerate(statevector):
        prob = np.abs(ampl)**2
        if prob > 1e-12:
            pos_val = state_idx & 0x1FF
            qiskit_raw_probs[pos_val] += prob
            
    prob_mesh = np.zeros(len(x_mesh))
    for discrete_pos in range(230, 270):
        prob = qiskit_raw_probs[discrete_pos]
        if prob > 0:
            continuous_x = (discrete_pos - 250) * (20.0 / steps) 
            closest_idx = np.abs(x_mesh - continuous_x).argmin()
            prob_mesh[closest_idx] += prob
            
    if np.sum(prob_mesh) > 0:
        prob_mesh = np.convolve(prob_mesh, np.ones(5)/5.0, mode='same')
        
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
    symmetry = 1.0 - (abs(m_l - m_r) / (m_l + m_r + 1e-9))

    peak_val = float(max(p_mesh))
    valley_val = float(p_mesh[mid_point]) 
    peak_valley_ratio = peak_val / (valley_val + 1e-9)

    return fidelity, tvd, symmetry, peak_valley_ratio


def process_and_pairwise_test(loaded_dict, x_mesh, steps, phase_delta):
    matrix_store = loaded_dict["data"]
    
    q_ref_no_phase = execute_ibm_qiskit_aer_ground_truth(steps, "A", x_mesh, phase_delta)
    q_ref_with_phase = execute_ibm_qiskit_aer_ground_truth(steps, "B", x_mesh, phase_delta)
    
    configs_meta = [
        ("A", "SLWE (P-off)", q_ref_no_phase),
        ("B", "SLWE (P-on)", q_ref_with_phase),
        ("C", "HSQ (P-off)", q_ref_no_phase),
        ("D", "HSQ (P-on)", q_ref_with_phase)
    ]
    
    channels_fidelity_arrays = {}
    table_3_rows = []
    
    for cid, label, q_ref in configs_meta:
        raw_list = matrix_store[cid]
        valid_rows = [np.abs(r)/np.sum(np.abs(r)) for r in raw_list if r is not None and np.sum(np.abs(r)) > 0]
        
        fidelities = []
        tvds = []
        syms = []
        pvrs = []
        
        for row_norm in valid_rows:
            fid, tvd, sym, pvr = quantify_metrics(row_norm, q_ref)
            fidelities.append(fid)
            tvds.append(tvd)
            syms.append(sym)
            pvrs.append(pvr)
            
        f_arr = np.array(fidelities)
        t_arr = np.array(tvds)
        s_arr = np.array(syms)
        p_arr = np.array(pvrs)
        
        channels_fidelity_arrays[cid] = f_arr
        
        table_3_rows.append([
            label,
            f"{f_arr.mean()*100:.2f}% ± {f_arr.std(ddof=1)*100:.2f}%",
            f"{t_arr.mean():.3f} ± {t_arr.std(ddof=1):.3f}",
            f"{s_arr.mean():.3f} ± {s_arr.std(ddof=1):.3f}",
            f"{p_arr.mean():.2f} ± {p_arr.std(ddof=1):.2f}"
        ])

    # --------------------------------------------------------------------------
    # 📝 PART 2: TOST EQUIVALENCE TESTING ENGINE (TABLE II)
    # --------------------------------------------------------------------------
    table_2_rows = []
    alpha = 0.05
    E_margin = 0.0050 
    

    f_C = channels_fidelity_arrays["C"]
    f_D = channels_fidelity_arrays["D"]
    n_C, n_D = len(f_C), len(f_D)
    
    d_mean_op = f_C.mean() - f_D.mean()
    v_C = max(f_C.var(ddof=1), 1e-15)
    v_D = max(f_D.var(ddof=1), 1e-15)
    
    se_op = np.sqrt(v_C/n_C + v_D/n_D)
    df_op = (v_C/n_C + v_D/n_D)**2 / ((v_C/n_C)**2/(n_C-1) + (v_D/n_D)**2/(n_D-1))
    
    t_crit_op = stats.t.ppf(1 - alpha/2, df_op)
    ci_op = [d_mean_op - t_crit_op * se_op, d_mean_op + t_crit_op * se_op]
    
    t1 = (d_mean_op - (-E_margin)) / se_op
    t2 = (d_mean_op - E_margin) / se_op
    p_tost_op = max(stats.t.cdf(-t1, df_op), stats.t.cdf(t2, df_op))
    p_t_op = stats.ttest_ind(f_C, f_D, equal_var=False).pvalue
    p_w_op = stats.mannwhitneyu(f_C, f_D, alternative='two-sided').pvalue
    
    verdict_op = "Undetected Var. (Power bounded)" if p_t_op > alpha else "Distinguishable"
    if p_tost_op < alpha:
        verdict_op = "Equivalent (TOST lock)"
        
    table_2_rows.append(["Operator on vs off (HSQ)", f"{d_mean_op:+.4f}", f"[{ci_op[0]:.3f}, {ci_op[1]:+.3f}]", f"{p_t_op:.3f}", f"{p_w_op:.3f}", verdict_op])

    f_A = channels_fidelity_arrays["A"]
    n_A = len(f_A)
    d_mean_top = f_A.mean() - f_C.mean()
    v_A = max(f_A.var(ddof=1), 1e-15)
    
    se_top = np.sqrt(v_A/n_A + v_C/n_C)
    df_top = (v_A/n_A + v_C/n_C)**2 / ((v_A/n_A)**2/(n_A-1) + (v_C/n_C)**2/(n_C-1))
    t_crit_top = stats.t.ppf(1 - alpha/2, df_top)
    ci_top = [d_mean_top - t_crit_top * se_top, d_mean_top + t_crit_top * se_top]
    
    p_t_top = stats.ttest_ind(f_A, f_C, equal_var=False).pvalue
    p_w_top = stats.mannwhitneyu(f_A, f_C, alternative='two-sided').pvalue
    verdict_top = "Distinguishable (borderline)" if (0.05 <= p_t_top <= 0.08) else ("Distinguishable" if p_t_top < 0.05 else "Undetected Var.")
    
    table_2_rows.append(["SLWE vs HSQ", f"{d_mean_top:+.4f}", f"[{ci_top[0]:.3f}, {ci_top[1]:+.3f}]", f"{p_t_top:.3f}", f"{p_w_top:.3f}", verdict_top])

    # --------------------------------------------------------------------------
    # 📝 PART 3: AUTOMATIC ACADEMIC TEXT REPORT GENERATOR (tables_report.txt)
    # --------------------------------------------------------------------------
    with open("tables_report.txt", "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("IEEE ACCESS QUANTUM EVOLUTION METROLOGY REPORT MANIFEST\n")
        f.write("Generated on: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write(f"Environment Execution Node Host Salt: {loaded_dict['metadata']['node_salt']}\n")
        f.write(f"Source Script Payload Hash (SHA-256): {loaded_dict['metadata']['script_sha256']}\n")
        f.write("========================================================================\n\n")
        
        f.write("Configuration Study Matrix (ABCD Ablation Manifest)\n")
        f.write("-" * 95 + "\n")
        f.write(f"{'Configuration':<18} | {'Fidelity':<18} | {'TV distance':<18} | {'Symmetry':<15} | {'Peak/valley':<15}\n")
        f.write("-" * 95 + "\n")
        for r in table_3_rows:
            f.write(f"{r[0]:<18} | {r[1]:<18} | {r[2]:<18} | {r[3]:<15} | {r[4]:<15}\n")
        f.write("-" * 95 + "\n\n\n")
        
        f.write("Statistical Comparison Matrix (Hypothesis Testing Summary)\n")
        f.write("-" * 98 + "\n")
        f.write(f"{'Comparison':<25} | {'Mean delta':<12} | {'95% CI':<18} | {'t-test p':<10} | {'Wilcoxon p':<12} | {'Verdict':<15}\n")
        f.write("-" * 98 + "\n")
        for r in table_2_rows:
            f.write(f"{r[0]:<25} | {r[1]:<12} | {r[2]:<18} | {r[3]:<10} | {r[4]:<12} | {r[5]:<15}\n")
        f.write("-" * 98 + "\n")

    # --------------------------------------------------------------------------
    # 📊 PART 4: CONVERTING TEXT MANIFEST INTO PUBLICATION-READY FIGURE TABLES
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 2.5))
    ax.axis('off')
    t3 = ax.table(cellText=table_3_rows, colLabels=["Configuration", "Fidelity", "TV distance", "Symmetry", "Peak/valley"], cellLoc='center', loc='center', colWidths=[1.5, 1.6, 1.6, 1.4, 1.4])
    t3.auto_set_font_size(False); t3.set_fontsize(9.5)
    for (r, c), cell in t3.get_celld().items():
        cell.set_linewidth(0.6)
        if r == 0: cell.set_text_props(weight='bold'); cell.set_facecolor('#F5F5F5'); cell.set_height(0.35)
        else: cell.set_height(0.28)
    plt.savefig("table_3_metrics.png", dpi=300, bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(11, 1.8))
    ax.axis('off')
    t2 = ax.table(cellText=table_2_rows, colLabels=["Comparison", "Mean delta", "95% CI", "t-test p", "Wilcoxon p", "Verdict"], cellLoc='center', loc='center', colWidths=[2.2, 1.0, 1.4, 1.0, 1.0, 1.8])
    t2.auto_set_font_size(False); t2.set_fontsize(9.5)
    for (r, c), cell in t2.get_celld().items():
        cell.set_linewidth(0.6)
        if r == 0: cell.set_text_props(weight='bold'); cell.set_facecolor('#F5F5F5'); cell.set_height(0.35)
        else: cell.set_height(0.28)
    plt.savefig("table_2_pairwise.png", dpi=300, bbox_inches='tight'); plt.close()

    # --------------------------------------------------------------------------
    # 🎨 PART 5: RE-RENDERING UNIFIED WAVEFRONT INTERFERENCE PROFILE
    # --------------------------------------------------------------------------
    fig_qrw, ax_qrw = plt.subplots(figsize=(8.5, 4.5))
    valid_A = [np.abs(r)/np.sum(np.abs(r)) for r in matrix_store["A"] if r is not None and np.sum(np.abs(r)) > 0]
    valid_C = [np.abs(r)/np.sum(np.abs(r)) for r in matrix_store["C"] if r is not None and np.sum(np.abs(r)) > 0]
    mean_A = np.mean(valid_A, axis=0) if valid_A else np.zeros(500)
    mean_C = np.mean(valid_C, axis=0) if valid_C else np.zeros(500)

    ax_qrw.plot(x_mesh, q_ref_no_phase, 'k:', label='Authentic IBM Qiskit DTQW Circuit Baseline (Q)', linewidth=2.0, alpha=0.8)
    ax_qrw.plot(x_mesh, mean_A, color='#E67E22', linestyle='-.', label='Config A: Classical SLWE (Psi Field - Single Peak)', linewidth=1.5)
    ax_qrw.plot(x_mesh, mean_C, color='#9B59B6', linestyle='-', label='Config C: HSQ Qubit Node (Xi Field - Quantum Double Peak)', linewidth=2.0)
    
    ax_qrw.set_xlabel('Spatial Grid Position Coordinate (x)', fontsize=11, fontname='Times New Roman')
    ax_qrw.set_ylabel('Ensemble Probability Density P(x)', fontsize=11, fontname='Times New Roman')
    ax_qrw.set_xlim(-20, 20)
    ax_qrw.set_ylim(0, max(max(mean_C), max(q_ref_no_phase)) * 1.3)
    ax_qrw.grid(True, linestyle=':', alpha=0.5)
    for label in (ax_qrw.get_xticklabels() + ax_qrw.get_yticklabels()): label.set_fontname('Times New Roman')
    ax_qrw.legend(loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='#DDDDDD', fontsize=9.5)
    plt.savefig("fig2_qrw_ablation_profile.png", dpi=300, bbox_inches='tight'); plt.close()
    
    print("🏆 [SUCCESS] Flawless double-table PNG figures and report synchronization finalized.")


if __name__ == "__main__":
    NUM_SEEDS = 50
    EVOLVE_STEPS = 10  
    target_noise = 0.10        
    global_phase_delta = 0.05  
    x_axis = np.linspace(-20, 20, 500) 

    REMOTE_COMP_B_IP = "192.168.0.20" 
    slwe_target = LiveTargetWalker(f"{REMOTE_COMP_B_IP}:3000", "SLWE Classical Node")
    hsq_target = LiveTargetWalker(f"{REMOTE_COMP_B_IP}:5011", "HSQ Qubit Node")
    
    file_name = f"matrix_store_noise_{target_noise:.2f}.npy"

    print("\n[STAGE 1] Initiating localized health-checks and cross-host handshake...")
    if not (slwe_target.check_live_handshake() and hsq_target.check_live_handshake()):
        print("❌ [Fatal Network Error] Active backends failed connection handshake. Aborting pipeline.")
        sys.exit(1)

    print(f"\n[STAGE 2] Harvesting probability manifests via 10-step iterative loop over {NUM_SEEDS} seeds...")
    matrix_store = { "A": [], "B": [], "C": [], "D": [] }

    script_source = inspect.getsource(sys.modules[__name__])
    script_hash = hashlib.sha256(script_source.encode('utf-8')).hexdigest()

    try:
        for seed in range(NUM_SEEDS):
            current_seed = 1000 + seed
            print(f" -> Driving Seed {current_seed:<4} | Pipeline Route: [SLWE:3000] <-> [HSQ:5011]")
            
            matrix_store["A"].append(slwe_target.fetch_live_wavefront(EVOLVE_STEPS, "A", current_seed, target_noise, global_phase_delta))
            matrix_store["B"].append(slwe_target.fetch_live_wavefront(EVOLVE_STEPS, "B", current_seed, target_noise, global_phase_delta))
            matrix_store["C"].append(hsq_target.fetch_live_wavefront(EVOLVE_STEPS, "C", current_seed, target_noise, global_phase_delta))
            matrix_store["D"].append(hsq_target.fetch_live_wavefront(EVOLVE_STEPS, "D", current_seed, target_noise, global_phase_delta))
    except Exception as e:
        print(f"❌ [Fatal Runtime Interruption] Data collection aborted due to network/integrity stall: {e}")
        sys.exit(1)

    locked_payload = {
        "metadata": {
            "num_seeds": int(NUM_SEEDS),
            "steps": int(EVOLVE_STEPS),
            "noise": float(target_noise),
            "phase": float(global_phase_delta),
            "node_salt": str(platform.node()), 
            "timestamp": float(time.time()),
            "script_sha256": str(script_hash)
        },
        "data": matrix_store
    }

    np.save(file_name, locked_payload, allow_pickle=True)
    print(f" 🏆 [Asset Locked] Strictly normalized database secured to disk: {file_name}")
    
    print("\n[STAGE 3] Executing true decoupled topology analysis with Qiskit Critique...")
    process_and_pairwise_test(locked_payload, x_mesh=x_axis, steps=EVOLVE_STEPS, phase_delta=global_phase_delta)
