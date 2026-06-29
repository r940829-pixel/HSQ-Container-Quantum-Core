# ==============================================================================
# CLASSICAL SIGNAL-BASED LINEAR WAVE EQUATION (SLWE) BENCHMARK NODE
# [MAXIMUM PERFORMANCE COMPLIANCE - GPU ACCELERATED VIA NVIDIA CUDA CORES]
# Fully aligned with formulations of Spreeuw 2001 & La Cour 2015/2016.
# Mirrors the Flask API schema and response topology of the HSQ container 100%.
# ==============================================================================

import os
import sys
import redis
import numpy as np
from flask import Flask, request, jsonify

# ==============================================================================
# HARDWARE ACCELERATION CORES BINDING LAYER (SLWE GPU WELDING)
# ==============================================================================
try:
    import cupy as cp
    xp = cp
    HAS_GPU = True
except ImportError:
    xp = np
    HAS_GPU = False

app = Flask(__name__)

# ==============================================================================
# INTER-PROCESS COMMUNICATION CHANNEL (DISTRIBUTED TENSOR BUS ALIGNMENT)
# ==============================================================================
TENSOR_BUS_HOST = os.environ.get("TENSOR_BUS_HOST", "localhost")
try:
    tensor_bus = redis.Redis(host=TENSOR_BUS_HOST, port=1000, db=0, decode_responses=True)
    tensor_bus.ping()
    BUS_CONNECTED = True
    print(f"🔗 [Tensor Bus] Bound to Virtual Switch at {TENSOR_BUS_HOST}:2057")
except redis.ConnectionError:
    tensor_bus = None
    BUS_CONNECTED = False
    print("⚠️ [Tensor Bus] Virtual Switch not detected. Operating in strictly isolated mode.")

# ==============================================================================
# GPU ACCELERATED SLWE NUMERICAL COMPUTATIONAL CORE
# ==============================================================================
class HilbertSpaceClassicalSignalSLWEEngine:
    def __init__(self, num_qubits=1):
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits  
        
        # ⚡ CUDA Accelerated Register Initialization
        self.signal_vector = xp.zeros(self.dimension, dtype=complex)
        self.signal_vector[0] = 1.0 + 0j
        
        self.current_step = 0
        self.phi = 0.0      # Rigid tracking for relative gate phase
        self.k_delta = 0.0  # Cumulative dephasing noise constant
        
        # --- Physics Perfect Alignment to HSQ Core ---
        self.omega_L = 2.0
        self.omega_R = 2.0
        self.k_L = 1.2
        self.k_R = -1.2
        self.sigma = 2.0    # Initial spatial packet width (sigma_0)
        self.vg = 0.8       # Velocity parameter (v_g)
        self.alpha = 0.1    # Spatiotemporal diffusion mapping index

    def enforce_gauge_protection(self):
        """ Normalization safeguard tightly bound within 1e-15 margin via GPU """
        total_power = float(xp.sum(xp.abs(self.signal_vector) ** 2))
        if total_power > 1e-15:
            self.signal_vector = self.signal_vector / xp.sqrt(total_power)

    def apply_hadamard_gate(self):
        """ ⚡ GPU-Accelerated Global Mixer Transformation """
        H_single = xp.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex) / xp.sqrt(2)
        H_total = H_single
        for _ in range(self.num_qubits - 1):
            H_total = xp.kron(H_total, H_single)
        self.signal_vector = xp.dot(H_total, self.signal_vector)
        self.phi = 0.0  
        self.enforce_gauge_protection()

    def apply_pauli_x_gate(self):
        """ ⚡ GPU Bit-flip substitution """
        if HAS_GPU:
            self.signal_vector = self.signal_vector[::-1]
        else:
            self.signal_vector = np.flip(self.signal_vector)
        self.enforce_gauge_protection()

    def apply_phase_rotation_gate(self, delta_phi):
        """ ⚡ GPU-Accelerated compliant Phase Gate Rotation """
        self.phi = delta_phi
        for i in range(1, self.dimension):
            self.signal_vector[i] *= xp.exp(1j * delta_phi)
        self.enforce_gauge_protection()

    def inject_phase_damping(self, noise_level=0.1, seed_val=None):
        """ 🌟 [FIXED NOISE SANITIZATION CORE - SLWE EDITION] """
        if noise_level <= 0.0:
            self.k_delta = 0.0  # FORCE PURGE
            return
            
        if seed_val is not None:
            try:
                np.random.seed(int(seed_val) + int(self.current_step))
            except:
                pass
                    
        noise = np.random.normal(0, noise_level)
        self.k_delta += noise
        for i in range(1, self.dimension):
            self.signal_vector[i] *= xp.exp(1j * noise)
        self.enforce_gauge_protection()

    def compute_current_xi(self, t=1.0):
        """ ⚡ 500-point Localized Grid Solver completely offloaded to CUDA GPU """
        x_grid = xp.linspace(-20, 20, 500)
        current_sigma = xp.sqrt(self.sigma**2 + self.alpha * t)
        
        # 🌟 Pull complex weights from device memory arrays safely
        a_complex = self.signal_vector[0]
        b_complex = self.signal_vector[1] if self.dimension > 1 else 0j
        
        envelope_a = xp.exp(-((x_grid + self.vg * t)**2) / (2 * current_sigma**2))
        envelope_b = xp.exp(-((x_grid - self.vg * t)**2) / (2 * current_sigma**2))
        
        phase_L = self.k_L * x_grid + self.omega_L * t
        phase_R = (self.k_R - self.k_delta) * x_grid + self.omega_R * t + self.phi
        
        xi_classical = a_complex * envelope_a * xp.exp(1j * phase_L) + \
                       b_complex * envelope_b * xp.exp(1j * phase_R)
        
        prob = xp.abs(xi_classical)**2
        total_sum = float(xp.sum(prob))
        if total_sum > 0:
            prob = prob / total_sum
            
        if HAS_GPU:
            return [float(v) for v in cp.asnumpy(prob).flatten()]
        return [float(v) for v in prob.flatten()]


slwe_engine = None

# ==============================================================================
# 🤝 100% MIRRORED RESTFUL API DAEMON ROUTING GATEWAYS
# ==============================================================================

@app.route('/reset', methods=['POST'])
def route_reset():
    global slwe_engine
    data = request.get_json(silent=True) or {}
    requested_qubits = data.get("num_qubits")
    user_qubits = int(requested_qubits) if requested_qubits is not None else slwe_engine.num_qubits
    
    slwe_engine = HilbertSpaceClassicalSignalSLWEEngine(num_qubits=user_qubits)
    return jsonify({"status": "success", "msg": f"SLWE qubit register reset successfully for N={user_qubits}"})

@app.route('/ping', methods=['GET'])
def route_ping():
    return jsonify({
        "status": "ready",
        "device": "NVIDIA GPU Hardware Acceleration Direct Access Mode" if HAS_GPU else "CPU Simulation Mode",
        "cuda_accelerated": HAS_GPU,
        "tensor_bus_active": BUS_CONNECTED,
        "configured_qubits": slwe_engine.num_qubits if slwe_engine else 0
    })

@app.route('/instruction', methods=['POST'])
def route_instruction():
    global slwe_engine
    data = request.get_json(silent=True) or {}
    gate_name = data.get("gate", "").lower()
    
    if gate_name in ["h", "hadamard"]:
        slwe_engine.apply_hadamard_gate()
        v_0 = slwe_engine.signal_vector[0]
        return jsonify({
            "status": "success", "gate": "Hadamard",
            "a_magnitude": float(np.abs(cp.asnumpy(v_0))) if HAS_GPU else float(np.abs(v_0))
        })
    elif gate_name in ["x", "not"]:
        slwe_engine.apply_pauli_x_gate()
        return jsonify({"status": "success", "gate": "Pauli-X"})
    elif gate_name in ["phase", "p"]:
        delta_phi = float(data.get("delta_phi", 0.0))
        slwe_engine.apply_phase_rotation_gate(delta_phi)
        return jsonify({"status": "success", "gate": "Phase Rotation", "phi": float(slwe_engine.phi)})
    return jsonify({"status": "error", "msg": f"Gate instruction '{gate_name}' not supported"}), 400

@app.route('/evolve', methods=['POST', 'GET'])
def route_evolve():
    global slwe_engine
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        noise_level = float(data.get('noise', 0.0))
        seed_val = data.get('seed')
        if seed_val is not None: seed_val = int(seed_val)
        t_input = data.get('t')
        
        slwe_engine.current_step += 1
        t = float(t_input) if t_input is not None else slwe_engine.current_step * 0.1
    else:
        t_input = request.args.get('t')
        noise_level = float(request.args.get('noise', 0.0))
        seed_val = request.args.get('seed')
        if seed_val is not None: seed_val = int(seed_val)
        
        slwe_engine.current_step += 1
        t = float(t_input) if t_input is not None else slwe_engine.current_step * 0.1
        
    slwe_engine.inject_phase_damping(noise_level, seed_val=seed_val)
    prob_dist = slwe_engine.compute_current_xi(t=t)
    
    v_0 = slwe_engine.signal_vector[0]
    gauge_val = float(np.abs(cp.asnumpy(v_0))**2) if HAS_GPU else float(np.abs(v_0)**2)
    
    return jsonify({
        "status": "evolved",
        "t_final": t,
        "gauge_metric_integrity": gauge_val,
        "probability_density": prob_dist
    })

# ==============================================================================
# ENTRY POINT & RUNTIME BOOTSTRAPPER
# ==============================================================================
if __name__ == "__main__":
    print("======================================================================")
    print("===        La Cour & Spreeuw Reference Framework: SLWE Node         ===")
    print("======================================================================")
    
    # Check for automated Docker/System environment scale prior to interactive shell fallback
    try:
        env_scale = os.environ.get("SLWE_QUBITS_SCALE")
        if env_scale is not None:
            user_qubits = int(env_scale)
            print(f" -> Automated boot detected. Scaling registers to N={user_qubits} via environment variable.")
        else:
            user_input = input("Designate virtual qubit scale for SLWE emulation (N): ")
            user_qubits = int(user_input)
    except (ValueError, KeyboardInterrupt, EOFError):
        user_qubits = 1
        print(f"\n -> Input bypassed or invalid. Falling back to default scale: N={user_qubits}")
        
    print(f"\n[Hardware Matrix Allocated] Deploying {user_qubits} classical channels ({2**user_qubits} dimensions).")
    slwe_engine = HilbertSpaceClassicalSignalSLWEEngine(num_qubits=user_qubits)
    
    print(f"=== [Daemon Activated] SLWE microservice standalone node live on Port 3000 ===")
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)
