# ==============================================================================
# 🌟 LA COUR 2015/2016 AUTHENTIC ANALOG RF BACKEND IMPLEMENTATION: slwe_local.py
# 🌟 [DYNAMIC REGISTRATION REFRACTOR - GPU ACCELERATED LAYER]
# ==============================================================================
import os
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================================================================
# ⚡ HARDWARE ACCELERATION BINDING LAYER (CUDA GPU DETECTION)
# ==============================================================================
try:
    import cupy as cp
    xp = cp
    HAS_GPU = True
    mempool = cp.get_default_memory_pool()
except ImportError:
    xp = np
    HAS_GPU = False

DEFAULT_GRID_SIZE = 500
GRID_SIZE = DEFAULT_GRID_SIZE
V_I = xp.zeros(GRID_SIZE, dtype=np.float64)
V_Q = xp.zeros(GRID_SIZE, dtype=np.float64)


OMEGA_C = 2.0  
K_L = 1.2      
K_R = -1.2     
V_G = 0.8      


V_I[GRID_SIZE // 2] = 1.0
V_Q[GRID_SIZE // 2] = 0.0

@app.route('/reset', methods=['POST'])
def hardware_reset():
    """ 🧹  """
    global V_I, V_Q, GRID_SIZE
    payload = request.get_json() if request.is_json else {}
    
    GRID_SIZE = int(payload.get("grid_size", DEFAULT_GRID_SIZE))
    
    V_I = xp.zeros(GRID_SIZE, dtype=np.float64)
    V_Q = xp.zeros(GRID_SIZE, dtype=np.float64)
    
    V_I[GRID_SIZE // 2] = 1.0  
    V_Q[GRID_SIZE // 2] = 0.0
    

    if HAS_GPU:
        mempool.free_all_blocks()
        
    core_mode = "NVIDIA CUDA GPU ACTIVE" if HAS_GPU else "CPU NATIVE MODE"
    print(f"🧹 [RF BACKEND RESET] 。size: {GRID_SIZE} Channels | point channal: [{core_mode}]")
    
    return jsonify({
        "status": "Analog Circuit Discharged & Reset", 
        "current_configured_grid": GRID_SIZE,
        "hardware_engine": core_mode
    }), 200

@app.route('/ping', methods=['GET'])
def handshake():
    global GRID_SIZE
    return jsonify({
        "status": "ready",
        "device": "La Cour 2015/2016 Real Carrier Analog Emulation Suite",
        "cuda_accelerated": HAS_GPU,
        "device_mode": "NVIDIA GPU (CuPy Acceleration Active)" if HAS_GPU else "CPU Native Mode",
        "active_grid_channels": GRID_SIZE 
    }), 200

@app.route('/instruction', methods=['POST'])
def analog_gate_network():
    """ 🎛️ """
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
        
        # 🌟 
        new_V_I = factor * (V_I * xp.cos(lo_phase) - V_Q * xp.sin(lo_phase))
        new_V_Q = factor * (V_I * xp.sin(lo_phase) + V_Q * xp.cos(lo_phase))
        
        V_I = (new_V_I + new_V_Q) / np.sqrt(2)
        V_Q = (new_V_I - new_V_Q) / np.sqrt(2)
        
        return jsonify({"message": "Analog Mixer Matrix Interlocked"}), 200
        
    return jsonify({"error": "Unknown RF Component Mode"}), 400

@app.route('/evolve', methods=['POST'])
def analog_space_evolution():
    """ 🌊  """
    global V_I, V_Q, GRID_SIZE
    payload = request.get_json()
    
    noise_v = float(payload.get("thermal_noise_v_rms", 0.05))
    seed = int(payload.get("stochastic_seed", 1000))
    dt = float(payload.get("integration_time_delta_t", 0.1))
    

    if HAS_GPU:
        cp.random.seed(seed)
    else:
        np.random.seed(seed)
    

    x_grid = xp.linspace(-20, 20, GRID_SIZE, dtype=np.float64)
    

    phase_L = K_L * x_grid + OMEGA_C * dt
    phase_R = K_R * x_grid + OMEGA_C * dt
    

    new_V_I = V_I * xp.cos(phase_L) - V_Q * xp.sin(phase_R)
    new_V_q = V_I * xp.sin(phase_L) + V_Q * xp.cos(phase_R)


    if HAS_GPU:
        thermal_noise_I = cp.random.normal(0, noise_v * np.sqrt(dt), GRID_SIZE)
        thermal_noise_Q = cp.random.normal(0, noise_v * np.sqrt(dt), GRID_SIZE)
    else:
        thermal_noise_I = np.random.normal(0, noise_v * np.sqrt(dt), GRID_SIZE)
        thermal_noise_Q = np.random.normal(0, noise_v * np.sqrt(dt), GRID_SIZE)
    
    V_I = new_V_I + thermal_noise_I
    V_Q = new_V_q + thermal_noise_Q
    

    power_density = (V_I**2 + V_Q**2)
    
    total_power = power_density.sum()
    if total_power > 1e-15:
        power_density = power_density / total_power
        
    if HAS_GPU:
        output_list = power_density.get().tolist()
    else:
        output_list = power_density.tolist()
        
    return jsonify({"probability_density": output_list}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
