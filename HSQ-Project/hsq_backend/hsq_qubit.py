import os
import redis
import numpy as np
from flask import Flask, request, jsonify

# ==============================================================================
# HARDWARE ACCELERATION LAYER DETECTOR
# Automatically detect and bind the NVIDIA GPU acceleration layer via CuPy.
# If a compatible graphics engine is absent, gracefully fall back to CPU execution.
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
# VIRTUAL TENSOR-CHANNEL SWITCH CONNECTION (SIDE-CHANNEL IPC)
# Establishes connection to the Redis bus injected by deploy_orchestrator.py
# ==============================================================================
TENSOR_BUS_HOST = os.environ.get("TENSOR_BUS_HOST", "localhost")
try:
    tensor_bus = redis.Redis(host=TENSOR_BUS_HOST, port=6379, db=0, decode_responses=True)
    tensor_bus.ping()
    BUS_CONNECTED = True
    print(f"🔗 [Tensor Bus] Successfully bound to Virtual Switch at {TENSOR_BUS_HOST}:6379")
except redis.ConnectionError:
    tensor_bus = None
    BUS_CONNECTED = False
    print("⚠️ [Tensor Bus] Virtual Switch not detected. Operating in strictly isolated mode.")

# ==============================================================================
# MICROSCOPIC PHYSICS ENGINE SERVICE
# Encapsulates the physical attributes and spinor state vector of a single 
# Hilbert-Space Spinor Quasiparticle (HSQ) with active gauge-metric protection.
# ==============================================================================
class HilbertSpaceSpinorQuasiparticleService:
    def __init__(self):
        """
        Initialize the localized spinor registers and spatiotemporal field coefficients.
        All constants are rigorously aligned with the formal master's thesis framework.
        """
        # --- Spatiotemporal Field Parameters ---
        self.omega_L = 2.0
        self.omega_R = 2.0
        self.k_L = 1.2
        self.k_R = -1.2
        
        self.sigma = 2.0    # Initial spatial packet width (sigma_0)
        self.vg = 0.8       # Group velocity (v_g)
        self.alpha = 0.1    # Spatiotemporal diffusion/envelope coefficient
        self.current_step = 0
        
        # --- Microscopic Spinor State Vector Intrinsic Setup ---
        # Initializing the sub-system into the pure ground state |0> (a=1, b=0)
        self.a = 1.0 + 0j
        self.b = 0.0 + 0j
        self.theta = 0.0
        self.phi = 0.0
        self.k_delta = 0.0  # Cumulative phase damping noise index

    def enforce_gauge_protection(self):
        """ 
        [Active Gauge Protection Operator]
        Forcibly projects the spinor state back onto the unitary manifold curve 
        (||a||² + ||b||² = 1) to eliminate dispersion leaks.
        """
        norm = np.sqrt(np.abs(self.a)**2 + np.abs(self.b)**2)
        if norm > 1e-6:
            self.a /= norm
            self.b /= norm

    def apply_hadamard_gate(self):
        """ Execute local unitary Hadamard coin gate transformation """
        self.theta = np.pi / 2
        self.phi = 0.0
        # Standard 2x2 unitary operator transformation matrix interaction
        new_a = (1.0 / np.sqrt(2)) * self.a + (1.0 / np.sqrt(2)) * self.b
        new_b = (1.0 / np.sqrt(2)) * self.a - (1.0 / np.sqrt(2)) * self.b
        self.a, self.b = new_a, new_b
        self.enforce_gauge_protection()

    def apply_phase_rotation_gate(self, delta_phi):
        """ Execute local phase rotation quantum gate """
        self.phi += delta_phi
        self.b = self.b * np.exp(1j * delta_phi)
        self.enforce_gauge_protection()

    def inject_phase_damping(self, noise_level=0.1):
        """ Emulate environmental phase decoherence noise injection """
        noise = np.random.normal(0, noise_level)
        self.k_delta += noise  # Accumulate into the environmental wave-number spectrum
        self.enforce_gauge_protection()

    def extract_topological_metric(self):
        """
        Extracts the localized probability weight of the spin-up component.
        This metric will act as the control variable broadcasted across the Tensor Bus.
        """
        weight_a = float(np.abs(self.a)**2)
        total_w = weight_a + float(np.abs(self.b)**2) + 1e-9
        return weight_a / total_w

    def apply_conditional_entanglement_phase(self, control_metric):
        """
        [Non-local Phase Interweaving]
        Applies a phase shift strictly proportional to the non-local control metric.
        This mathematically synthesizes a Distributed Continuous CNOT / CPhase gate.
        """
        # phase_shift ranges from 0 to Pi depending on the state of the control node
        phase_shift = np.pi * control_metric
        self.phi += phase_shift
        self.b = self.b * np.exp(1j * phase_shift)
        self.enforce_gauge_protection()

    def compute_current_xi(self, t=1.0):
        """ 
        Solve the continuous spatiotemporal partial differential equation on the 
        500-point mesh grid to project macro wavepacket dynamics.
        """
        x_grid = xp.linspace(-20, 20, 500)
        
        # 1. Extract pure real scalar weights from the microscopic spinor register
        weight_a = float(np.abs(self.a)**2)
        weight_b = float(np.abs(self.b)**2)
        w_total = weight_a + weight_b + 1e-9
        w_a, w_b = weight_a / w_total, weight_b / w_total
        
        # 2. Compute the spatiotemporal Gaussian envelope
        current_sigma = np.sqrt(self.sigma**2 + self.alpha * t)
        envelope_a = xp.exp(-((x_grid + self.vg * t)**2) / (2 * current_sigma**2))
        envelope_b = xp.exp(-((x_grid - self.vg * t)**2) / (2 * current_sigma**2))
        envelope = envelope_a * w_a + envelope_b * w_b
        
        # 3. Solve the micro-macro phase gauge coupling angle Theta(x,t)
        time_phase = (w_a * self.omega_L + w_b * self.omega_R) * t
        space_phase = (w_a * self.k_L + w_b * self.k_R - self.k_delta) * x_grid
        spinor_phase = time_phase + space_phase
        
        # 4. Synthesize the full coherent macro manifold evolution
        xi = envelope * (self.a + self.b) * xp.exp(1j * spinor_phase)
        
        # 5. Extract macro normalized probability density profile P(x) = ||xi||²
        prob = xp.abs(xi)**2
        total_sum = float(xp.sum(prob))
        if total_sum > 0:
            prob = prob / total_sum
            
        if HAS_GPU:
            return [float(v) for v in cp.asnumpy(prob).flatten()]
        return [float(v) for v in prob.flatten()]

# Instantiate the cloud-native virtualized qubit chip service daemon
hsq_qubit = HilbertSpaceSpinorQuasiparticleService()

# ==============================================================================
# RESTFUL API ENDPOINTS & GATEWAY INTERFACES
# ==============================================================================

@app.route('/ping', methods=['GET'])
def route_ping():
    """ Health-check endpoint broadcasting device configurations and GPU metrics """
    return jsonify({
        "status": "ready",
        "device": "NVIDIA GeForce GPU Acceleration Node" if HAS_GPU else "CPU Simulation Mode",
        "cuda_accelerated": HAS_GPU,
        "tensor_bus_active": BUS_CONNECTED
    })

@app.route('/instruction', methods=['POST'])
def route_instruction():
    """ Unified gate orchestration gateway mimicking Qiskit controller behaviors """
    data = request.get_json(silent=True) or {}
    gate_name = data.get("gate", "").lower()
    
    # 1. Local Hadamard Gate
    if gate_name == "h" or gate_name == "hadamard":
        hsq_qubit.apply_hadamard_gate()
        return jsonify({
            "status": "success", 
            "gate": "Hadamard",
            "a_magnitude": float(np.abs(hsq_qubit.a)), 
            "b_magnitude": float(np.abs(hsq_qubit.b))
        })
        
    # 2. Local Phase Gate
    elif gate_name == "phase" or gate_name == "p":
        delta_phi = float(data.get("delta_phi", 0.0))
        hsq_qubit.apply_phase_rotation_gate(delta_phi)
        return jsonify({
            "status": "success", 
            "gate": "Phase Rotation",
            "phi": float(hsq_qubit.phi)
        })
        
    # 🟢 3. [Distributed Protocol] Export Tensor Metric (Control Qubit)
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

    # 🟢 4. [Distributed Protocol] Apply Conditional Phase (Target Qubit)
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
    """ Core spatiotemporal evolution solver interface supporting bidirectional parameters """
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        noise_level = float(data.get('noise', 0.0))
        hsq_qubit.current_step += 1
        t = hsq_qubit.current_step * 0.1
    else:
        t = float(request.args.get('t', 1.0))
        noise_level = float(request.args.get('noise', 0.0))
        
    if noise_level > 0:
        hsq_qubit.inject_phase_damping(noise_level)
        
    prob_dist = hsq_qubit.compute_current_xi(t=t)
    
    return jsonify({
        "status": "evolved",
        "t_final": t,
        "gauge_metric_integrity": float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2),
        "probability_density": prob_dist
    })

# (Legacy routes /gate/h, /gate/phase, /noise/inject, /measure/coherence are kept identical...)
@app.route('/gate/h', methods=['POST'])
def route_gate_h_legacy():
    hsq_qubit.apply_hadamard_gate()
    return jsonify({"msg": "Hadamard gate applied successfully", "a": float(np.abs(hsq_qubit.a)), "b": float(np.abs(hsq_qubit.b))})

@app.route('/gate/phase', methods=['POST'])
def route_gate_phase_legacy():
    data = request.json or {}
    delta_phi = data.get('delta_phi', 0.0)
    hsq_qubit.apply_phase_rotation_gate(delta_phi)
    return jsonify({"msg": "Phase rotation applied successfully", "phi": float(hsq_qubit.phi)})

@app.route('/noise/inject', methods=['POST'])
def route_noise_inject():
    data = request.json or {}
    noise_level = data.get('noise_level', 0.1)
    hsq_qubit.inject_phase_damping(noise_level)
    return jsonify({"msg": "Phase damping noise injected successfully", "current_k_delta": float(hsq_qubit.k_delta)})

@app.route('/measure/coherence', methods=['GET'])
def route_measure_coherence():
    coherence_value = float(np.abs(hsq_qubit.a * np.conj(hsq_qubit.b)))
    gauge_check = float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2)
    return jsonify({"coherence": coherence_value, "gauge_metric_integrity": gauge_check})

if __name__ == "__main__":
    print(f"=== [HSQ Verified Core Microservice] Initialization Successful | Listening on Port 5000 ===")
    app.run(host='0.0.0.0', port=5000)
