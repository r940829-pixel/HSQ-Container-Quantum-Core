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
OMEGA_C = 2.0  
K_L = 1.2      
K_R = -1.2     
V_G = 0.8      

CARRIER_PERIOD_T = (2.0 * np.pi) / OMEGA_C

t_accumulated = 0.0
noise_accumulated = 0.0

V_I[GRID_SIZE // 2] = 1.0
V_Q[GRID_SIZE // 2] = 0.0

@app.route('/reset', methods=['POST'])
def hardware_reset():
    global V_I, V_Q, GRID_SIZE, t_accumulated, noise_accumulated
    payload = request.get_json() if request.is_json else {}
    
    GRID_SIZE = int(payload.get("grid_size", DEFAULT_GRID_SIZE))
    
    V_I = xp.zeros(GRID_SIZE, dtype=np.float64)
    V_Q = xp.zeros(GRID_SIZE, dtype=np.float64)
    V_I[GRID_SIZE // 2] = 1.0  
    V_Q[GRID_SIZE // 2] = 0.0
    
    t_accumulated = 0.0
    noise_accumulated = 0.0

    if HAS_GPU:
        mempool.free_all_blocks()
        
    print(f"🧹 [RF BACKEND RESET] Grid Scaled to 512 | Central Anchor: {GRID_SIZE // 2}")
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
    global V_I, V_Q, GRID_SIZE
    payload = request.get_json()
    mode = payload.get("circuit_mode")
    
    if mode == "analog_carrier_injection":
        GRID_SIZE = int(payload.get("grid_size", GRID_SIZE))
        v_i = float(payload.get("injection_voltage_v_i", 1.0))
        v_q = float(payload.get("injection_voltage_v_q", 0.0))
        
        V_I = xp.zeros(GRID_SIZE, dtype=np.float64)
        V_Q = xp.zeros(GRID_SIZE, dtype=np.float64)
        V_I[GRID_SIZE // 2] = v_i
        V_Q[GRID_SIZE // 2] = v_q 
        return jsonify({"message": "Carrier Injection Terminated", "grid_size": GRID_SIZE}), 200
        
    elif mode == "configure_analog_mixer_network":
        att_db = float(payload.get("attenuation_coefficient_db", 3.0))
        lo_phase = float(payload.get("local_oscillator_phase_shift", 0.0))
        factor = 10 ** (-att_db / 20.0)
        
        new_V_I = factor * (V_I * xp.cos(lo_phase) - V_Q * xp.sin(lo_phase))
        new_V_Q = factor * (V_I * xp.sin(lo_phase) + V_Q * xp.cos(lo_phase))
        
        V_I = (new_V_I + new_V_Q) / np.sqrt(2)
        V_Q = (new_V_I - new_V_Q) / np.sqrt(2)
        return jsonify({"message": "Analog Mixer Matrix Interlocked"}), 200
        
    return jsonify({"error": "Unknown RF Component Mode"}), 400

@app.route('/evolve', methods=['POST'])
def analog_space_evolution():
    global V_I, V_Q, GRID_SIZE, t_accumulated, noise_accumulated
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

    x_grid = xp.linspace(-20, 20, GRID_SIZE, dtype=np.float64)
    
    integration_samples = 100
    t_prime = xp.linspace(t_accumulated - CARRIER_PERIOD_T, t_accumulated, integration_samples, dtype=np.float64)
    dt_prime = CARRIER_PERIOD_T / float(integration_samples)

    accumulated_I = xp.zeros(GRID_SIZE, dtype=np.float64)
    accumulated_Q = xp.zeros(GRID_SIZE, dtype=np.float64)

    for tp in t_prime:
        
        phase_L_dynamic = (K_L - noise_accumulated) * x_grid * V_G * tp
        phase_R_dynamic = (K_R - noise_accumulated) * x_grid * V_G * tp
        
        psi_R_t_prime = V_I * xp.cos(phase_L_dynamic) - V_Q * xp.sin(phase_R_dynamic)
        psi_I_t_prime = V_I * xp.sin(phase_L_dynamic) + V_Q * xp.cos(phase_R_dynamic)
        
        # 3. s(t') = psi_R(t')*cos(w_c*t') - psi_I(t')*sin(w_c*t')
        s_t_prime = psi_R_t_prime * xp.cos(OMEGA_C * tp) - psi_I_t_prime * xp.sin(OMEGA_C * tp)
        
        accumulated_I += (2.0 * xp.cos(OMEGA_C * tp) * s_t_prime) * dt_prime
        accumulated_Q += (-2.0 * xp.sin(OMEGA_C * tp) * s_t_prime) * dt_prime

    noise_floor = 1e-12
    if HAS_GPU:
        v_floor_I = cp.random.normal(0, noise_floor, GRID_SIZE)
        v_floor_Q = cp.random.normal(0, noise_floor, GRID_SIZE)
    else:
        v_floor_I = np.random.normal(0, noise_floor, GRID_SIZE)
        v_floor_Q = np.random.normal(0, noise_floor, GRID_SIZE)

    V_I = (accumulated_I / CARRIER_PERIOD_T) + v_floor_I
    V_Q = (accumulated_Q / CARRIER_PERIOD_T) + v_floor_Q

    power_density = (V_I**2 + V_Q**2)
    total_power = power_density.sum()
    if total_power > 1e-15:
        power_density = power_density / total_power
    else:
        power_density = xp.ones(GRID_SIZE, dtype=np.float64) / GRID_SIZE
        
    if HAS_GPU:
        output_list = power_density.get().tolist()
    else:
        output_list = power_density.tolist()
        
    return jsonify({"probability_density": output_list}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
