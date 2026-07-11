# ==============================================================================
# 🌟 LA COUR 2015/2016 AUTHENTIC ANALOG RF BACKEND IMPLEMENTATION: slwe_local.py
# 🌟 [🔥 SPECTRAL FREQUENCY-DIVISION MULTIPLEXING ENGINE - TRUE ORIGINAL VERSION]
# 1:1 Aligned with La Cour's exact time-domain signal synthesis and spectral 
# coherent demodulation. No space grid, pure frequency channel shift.
# ==============================================================================
import os
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

try:
    import cupy as cp
    xp = cp
    HAS_GPU = True
    mempool = cp.get_default_memory_pool()
except ImportError:
    xp = np
    HAS_GPU = False

DEFAULT_GRID_SIZE = 512
GRID_SIZE = DEFAULT_GRID_SIZE


V_I = xp.zeros(GRID_SIZE, dtype=np.float64)
V_Q = xp.zeros(GRID_SIZE, dtype=np.float64)

# 🌊 
OMEGA_C = 20.0       
DELTA_OMEGA = 0.5    
CARRIER_PERIOD_T = (2.0 * np.pi) / DELTA_OMEGA  

t_accumulated = 0.0
noise_accumulated = 0.0


current_gate_factor = 1.0          
current_lo_phase_shift = 0.0       


V_I[GRID_SIZE // 2] = 1.0
V_Q[GRID_SIZE // 2] = 0.0

@app.route('/reset', methods=['POST'])
def hardware_reset():
    global V_I, V_Q, GRID_SIZE, t_accumulated, noise_accumulated, current_gate_factor, current_lo_phase_shift
    payload = request.get_json() if request.is_json else {}
    
    GRID_SIZE = int(payload.get("grid_size", DEFAULT_GRID_SIZE))
    
    V_I = xp.zeros(GRID_SIZE, dtype=np.float64)
    V_Q = xp.zeros(GRID_SIZE, dtype=np.float64)
    V_I[GRID_SIZE // 2] = 1.0  
    V_Q[GRID_SIZE // 2] = 0.0
    
    t_accumulated = 0.0
    noise_accumulated = 0.0
    current_gate_factor = 1.0
    current_lo_phase_shift = 0.0

    if HAS_GPU:
        mempool.free_all_blocks()
        
    print(f"🧹 [RF BACKEND RESET] La Cour FDM Channel Array Initialized. Size: {GRID_SIZE}")
    return jsonify({
        "status": "Analog Circuit Discharged & Reset", 
        "current_configured_grid": GRID_SIZE
    }), 200

@app.route('/ping', methods=['GET'])
def handshake():
    global GRID_SIZE
    return jsonify({"status": "ready", "active_grid_channels": GRID_SIZE}), 200

@app.route('/instruction', methods=['POST'])
def analog_gate_network():
    global V_I, V_Q, GRID_SIZE, current_gate_factor, current_lo_phase_shift
    payload = request.get_json()
    mode = payload.get("circuit_mode")
    
    if mode == "analog_carrier_injection":
        GRID_SIZE = int(payload.get("grid_size", GRID_SIZE))
        V_I = xp.zeros(GRID_SIZE, dtype=np.float64)
        V_Q = xp.zeros(GRID_SIZE, dtype=np.float64)
        V_I[GRID_SIZE // 2] = float(payload.get("injection_voltage_v_i", 1.0))
        V_Q[GRID_SIZE // 2] = float(payload.get("injection_voltage_v_q", 0.0))
        return jsonify({"message": "Carrier Injection Terminated", "grid_size": GRID_SIZE}), 200
        
    elif mode == "configure_analog_mixer_network":
        att_db = float(payload.get("attenuation_coefficient_db", 3.0))
        current_lo_phase_shift = float(payload.get("local_oscillator_phase_shift", 0.0))
        current_gate_factor = 10 ** (-att_db / 20.0)
        return jsonify({"message": "Analog Mixer Matrix Interlocked"}), 200
        
    return jsonify({"error": "Unknown RF Component Mode"}), 400

@app.route('/evolve', methods=['POST'])
def analog_space_evolution():
    """ 
    🌊 
    """
    global V_I, V_Q, GRID_SIZE, t_accumulated, noise_accumulated, current_gate_factor, current_lo_phase_shift
    payload = request.get_json()
    
    noise_v = float(payload.get("thermal_noise_v_rms", 0.05))
    seed = int(payload.get("stochastic_seed", 1000))
    dt = float(payload.get("integration_time_delta_t", 0.1))
    
    t_accumulated += dt

    if HAS_GPU:
        cp.random.seed(seed)
        step_noise = float(cp.random.normal(0, noise_v * np.sqrt(dt)))
    else:
        np.random.seed(seed)
        step_noise = float(np.random.normal(0, noise_v * np.sqrt(dt)))
    noise_accumulated += step_noise


    k_axis = xp.arange(GRID_SIZE, dtype=np.float64)
    omega_k = OMEGA_C + (k_axis - (GRID_SIZE // 2)) * DELTA_OMEGA


    integration_samples = 100
    t_prime = xp.linspace(t_accumulated - CARRIER_PERIOD_T, t_accumulated, integration_samples, dtype=np.float64)
    dt_prime = CARRIER_PERIOD_T / float(integration_samples)

    accumulated_I = xp.zeros(GRID_SIZE, dtype=np.float64)
    accumulated_Q = xp.zeros(GRID_SIZE, dtype=np.float64)


    for tp in t_prime:

        V_I_rot = current_gate_factor * (V_I * xp.cos(current_lo_phase_shift) - V_Q * xp.sin(current_lo_phase_shift))
        V_Q_rot = current_gate_factor * (V_I * xp.sin(current_lo_phase_shift) + V_Q * xp.cos(current_lo_phase_shift))
        V_I_coin = (V_I_rot + V_Q_rot) / np.sqrt(2)
        V_Q_coin = (V_I_rot - V_Q_rot) / np.sqrt(2)
        

        phase_damping_noise = noise_accumulated * (k_axis - (GRID_SIZE // 2)) * dt
        

        s_t_prime = xp.sum(
            V_I_coin * xp.cos(omega_k * tp + phase_damping_noise) - 
            V_Q_coin * xp.sin(omega_k * tp + phase_damping_noise)
        )
        

        accumulated_I += (2.0 * xp.cos((omega_k - DELTA_OMEGA) * tp) * s_t_prime) * dt_prime
        accumulated_Q += (-2.0 * xp.sin((omega_k + DELTA_OMEGA) * tp) * s_t_prime) * dt_prime

    noise_floor = 1e-12
    if HAS_GPU:
        v_floor_I = cp.random.normal(0, noise_floor, GRID_SIZE)
        v_floor_Q = cp.random.normal(0, noise_floor, GRID_SIZE)
    else:
        v_floor_I = np.random.normal(0, noise_floor, GRID_SIZE)
        v_floor_Q = np.random.normal(0, noise_floor, GRID_SIZE)

    #  ψ_k = V_I_k + i*V_Q_k
    V_I = (accumulated_I / CARRIER_PERIOD_T) + v_floor_I
    V_Q = (accumulated_Q / CARRIER_PERIOD_T) + v_floor_Q

    if HAS_GPU:
        out_I = V_I.get().tolist()
        out_Q = V_Q.get().tolist()
    else:
        out_I = V_I.tolist()
        out_Q = V_Q.tolist()
        
    return jsonify({
        "psi_real": out_I,
        "psi_imag": out_Q
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
