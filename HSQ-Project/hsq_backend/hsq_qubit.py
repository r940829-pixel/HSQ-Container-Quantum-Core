# ==============================================================================
# HILBERT-SPACE SPINOR QUASIPARTICLE (HSQ) COMPUTATIONAL MICROSERVICE
# [REFACTORED FOR RIGOROUS ACADEMIC STANDARDS AND SINGLE-SOURCE FREQUENCY WELDED]
# Contains the numeric state register, GPU-accelerated spatial map solver, 
# and localized gate orchestration APIs for a single logic qubit emulator node.
# Fully aligned with the single-source constraint: omega_L = omega_R = omega_0.
# ==============================================================================

import os
import redis
import numpy as np
from flask import Flask, request, jsonify

# ==============================================================================
# HARDWARE ACCELERATION CORES BINDING LAYER
# Detects and binds NVIDIA GPU resources via CuPy. Falls back to CPU if unavailable.
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
# INTER-PROCESS COMMUNICATION CHANNEL (DISTRIBUTED TENSOR BUS)
# Binds the node to the shared Redis instance orchestrated by the controller link.
# ==============================================================================
TENSOR_BUS_HOST = os.environ.get("TENSOR_BUS_HOST", "localhost")
try:
    tensor_bus = redis.Redis(host=TENSOR_BUS_HOST, port=6379, db=0, decode_responses=True)
    tensor_bus.ping()
    BUS_CONNECTED = True
    print(f"🔗 [Tensor Bus] Bound to Virtual Switch at {TENSOR_BUS_HOST}:6379")
except redis.ConnectionError:
    tensor_bus = None
    BUS_CONNECTED = False
    print("⚠️ [Tensor Bus] Virtual Switch not detected. Operating in strictly isolated mode.")

# ==============================================================================
# NUMERICAL COMPUTATIONAL SOLVER CORE
# Encapsulates state vector evolutions and step-by-step normalization constraints
# to guarantee computational stability under randomized noise conditions.
# ==============================================================================
class HilbertSpaceSpinorQuasiparticleService:
    def __init__(self):
        """
        Initialize the complex state registers and spatiotemporal tracking coefficients.
        """
        # --- 🌟 SINGLE-SOURCE FREQUENCY BINDING ---
        # Rigorously welded into a single unified origin frequency baseline
        self.omega_0 = 2.0  # Replaces separate omega_L and omega_R constraints
        
        self.k_L = 1.2
        self.k_R = -1.2
        
        self.sigma = 2.0    # Initial spatial packet width (sigma_0)
        self.vg = 0.8       # Velocity parameter (v_g)
        self.alpha = 0.1    # Spatiotemporal diffusion mapping index
        self.current_step = 0
        
        # --- Multi-Component Complex State Vector ---
        self.a = 1.0 + 0j
        self.b = 0.0 + 0j
        self.theta = 0.0
        self.phi = 0.0
        self.k_delta = 0.0  # Cumulative random phase damping noise

    def enforce_gauge_protection(self):
        """ Maintains numerical stability, keeping values inside the unitary hypersphere. """
        norm = np.sqrt(np.abs(self.a)**2 + np.abs(self.b)**2)
        if norm > 1e-15:
            self.a /= norm
            self.b /= norm

    def apply_hadamard_gate(self):
        self.theta = np.pi / 2
        self.phi = 0.0
        new_a = (1.0 / np.sqrt(2)) * self.a + (1.0 / np.sqrt(2)) * self.b
        new_b = (1.0 / np.sqrt(2)) * self.a - (1.0 / np.sqrt(2)) * self.b
        self.a, self.b = new_a, new_b
        self.enforce_gauge_protection()

    def apply_pauli_x_gate(self):
        self.a, self.b = self.b, self.a
        self.enforce_gauge_protection()

    def apply_phase_rotation_gate(self, delta_phi):
        self.phi = delta_phi
        self.b = self.b * np.exp(1j * delta_phi)
        self.enforce_gauge_protection()

    def inject_phase_damping(self, noise_level=0.1, seed_val=None):
        if seed_val_str := seed_val:
            try:
                np.random.seed(int(seed_val_str) + int(self.current_step))
            except (ValueError, TypeError):
                pass
            
        noise = np.random.normal(0, noise_level)
        self.k_delta += noise  
        self.enforce_gauge_protection()

    def extract_topological_metric(self):
        weight_a = float(np.abs(self.a)**2)
        total_w = weight_a + float(np.abs(self.b)**2) + 1e-9
        return weight_a / total_w

    def apply_conditional_entanglement_phase(self, control_metric):
        phase_shift = np.pi * control_metric
        self.phi = phase_shift
        self.b = self.b * np.exp(1j * phase_shift)
        self.enforce_gauge_protection()

    def compute_current_xi(self, t=1.0):
        """ Solves the spatiotemporal evolution equation over a 500-point localized grid """
        x_grid = xp.linspace(-20, 20, 500)
        
        # 1. Harvest component weights from state registers
        weight_a = float(np.abs(self.a)**2)
        weight_b = float(np.abs(self.b)**2)
        w_total = weight_a + weight_b + 1e-9
        w_a, w_b = weight_a / w_total, weight_b / w_total
        
        # 2. Compute the spatiotemporal Gaussian envelope
        current_sigma = np.sqrt(self.sigma**2 + self.alpha * t)
        envelope_a = xp.exp(-((x_grid + self.vg * t)**2) / (2 * current_sigma**2))
        envelope_b = xp.exp(-((x_grid - self.vg * t)**2) / (2 * current_sigma**2))
        envelope = envelope_a * w_a + envelope_b * w_b
        
        # 3. Formulate the simplified single-source time phase index
        # 🌟 [CRITICAL REFACTORED] Simplified because w_a*omega_0 + w_b*omega_0 = omega_0
        time_phase = self.omega_0 * (w_a + w_b) * t
        
        space_phase = (w_a * self.k_L + w_b * self.k_R - self.k_delta) * x_grid + (w_b * self.phi)
        composite_phase = time_phase + space_phase
        
        # 4. Extrapolate macro continuous wave distribution profile
        xi = envelope * (self.a + self.b) * xp.exp(1j * composite_phase)
        
        # 5. Extract normalized probability density distribution mapping
        prob = xp.abs(xi)**2
        total_sum = float(xp.sum(prob))
        if total_sum > 0:
            prob = prob / total_sum
            
        if HAS_GPU:
            return [float(v) for v in cp.asnumpy(prob).flatten()]
        return [float(v) for v in prob.flatten()]


hsq_qubit = HilbertSpaceSpinorQuasiparticleService()

# ==============================================================================
# RESTFUL API ENDPOINTS & DAEMON ROUTING GATEWAYS
# ==============================================================================

@app.route('/reset', methods=['POST'])
def route_reset():
    global hsq_qubit
    if hsq_qubit:
        hsq_qubit.a = 1.0 + 0j
        hsq_qubit.b = 0.0 + 0j
        hsq_qubit.theta = 0.0
        hsq_qubit.phi = 0.0
        hsq_qubit.k_delta = 0.0
        hsq_qubit.current_step = 0
    return jsonify({"status": "success", "msg": "HSQ qubit register reset successfully"})

@app.route('/ping', methods=['GET'])
def route_ping():
    return jsonify({
        "status": "ready",
        "device": "NVIDIA GPU Hardware Acceleration Direct Access Mode" if HAS_GPU else "CPU Simulation Mode",
        "cuda_accelerated": HAS_GPU,
        "tensor_bus_active": BUS_CONNECTED
    })

@app.route('/instruction', methods=['POST'])
def route_instruction():
    data = request.get_json(silent=True) or {}
    gate_name = data.get("gate", "").lower()
    
    if gate_name in ["h", "hadamard"]:
        hsq_qubit.apply_hadamard_gate()
        return jsonify({
            "status": "success", 
            "gate": "Hadamard",
            "a_magnitude": float(np.abs(hsq_qubit.a)), 
            "b_magnitude": float(np.abs(hsq_qubit.b))
        })

    elif gate_name in ["x", "not"]:
        hsq_qubit.apply_pauli_x_gate()
        return jsonify({
            "status": "success",
            "gate": "Pauli-X",
            "a_magnitude": float(np.abs(hsq_qubit.a)),
            "b_magnitude": float(np.abs(hsq_qubit.b))
        })
        
    elif gate_name in ["phase", "p"]:
        delta_phi = float(data.get("delta_phi", 0.0))
        hsq_qubit.apply_phase_rotation_gate(delta_phi)
        return jsonify({
            "status": "success", 
            "gate": "Phase Rotation",
            "phi": float(hsq_qubit.phi)
        })
        
    elif gate_name == "export_tensor_metric":
        bus_key = data.get("bus_key")
        if not bus_key or not BUS_CONNECTED:
            return jsonify({"status": "error", "msg": "Missing bus_key or Tensor Bus disconnected"}), 400
        
        metric_val = hsq_qubit.extract_topological_metric()
        tensor_bus.set(bus_key, str(metric_val))
        return jsonify({
            "status": "success",
            "gate": "Export Tensor Metric",
            "exported_metric": metric_val
        })

    elif gate_name == "apply_conditional_phase":
        source_bus_key = data.get("source_bus_key")
        if not source_bus_key or not BUS_CONNECTED:
            return jsonify({"status": "error", "msg": "Missing source_bus_key or Tensor Bus disconnected"}), 400
            
        control_metric_str = tensor_bus.get(source_bus_key)
        if control_metric_str is None:
            return jsonify({"status": "error", "msg": f"Metric {source_bus_key} not found on Tensor Bus"}), 404
            
        control_metric = float(control_metric_str)
        hsq_qubit.apply_conditional_entanglement_phase(control_metric)
        
        return jsonify({
            "status": "success",
            "gate": "Conditional Phase Intersection",
            "applied_phase_shift": float(np.pi * control_metric),
            "a_magnitude": float(np.abs(hsq_qubit.a)),
            "b_magnitude": float(np.abs(hsq_qubit.b))
        })

    return jsonify({"status": "error", "msg": f"Gate instruction '{gate_name}' not natively supported"}), 400

@app.route('/evolve', methods=['POST', 'GET'])
def route_evolve():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        noise_level = float(data.get('noise', 0.0))
        seed_val = data.get('seed')
        if seed_val is not None: seed_val = int(seed_val)
            
        hsq_qubit.current_step += 1
        t = hsq_qubit.current_step * 0.1
    else:
        t = float(request.args.get('t', 1.0))
        noise_level = float(request.args.get('noise', 0.0))
        seed_val = request.args.get('seed')
        if seed_val is not None: seed_val = int(seed_val)
        
    if noise_level > 0:
        hsq_qubit.inject_phase_damping(noise_level, seed_val=seed_val)
        
    prob_dist = hsq_qubit.compute_current_xi(t=t)
    
    return jsonify({
        "status": "evolved",
        "t_final": t,
        "gauge_metric_integrity": float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2),
        "probability_density": prob_dist
    })

if __name__ == "__main__":
    print(f"=== [HSQ Verified Core Microservice] Initialization Successful | Listening on Port 5000 ===")
    app.run(host='0.0.0.0', port=5000)
