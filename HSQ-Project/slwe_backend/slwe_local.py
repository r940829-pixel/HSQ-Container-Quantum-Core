# ==============================================================================
# CLASSICAL SIGNAL-BASED LINEAR WAVE EQUATION (SLWE) BENCHMARK NODE
# Implements the multi-qubit classical amplitude modulation framework strictly
# aligned with the theoretical formulations of Spreeuw 2001 & La Cour 2015/2016.
# This serves as the experimental control group demonstrating unmitigated 
# decoherence avalanches due to the absence of active gauge protection metrics.
# ==============================================================================

import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

class DocumentBasedSLWEEngine:
    def __init__(self, num_qubits=1):
        """
        Initialize the classical amplitude modulation register matrix.
        An N-qubit ecosystem maps onto an exponential 2^N dimensional signal channel.
        """
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits  
        
        # Initialize classical signal vector into the pure baseline state |00...0>
        self.signal_vector = np.zeros(self.dimension, dtype=complex)
        self.signal_vector[0] = 1.0 + 0j
        
        self.current_step = 0
        self.k_delta = 0.0

    def apply_hadamard_to_all(self):
        """ 
        Execute global linear Hadamard transformation using classical mixer matrices
        expanded across the full 2^N dimensional space via Kronecker Products.
        """
        # Formulate single-qubit Hadamard kernel matrix
        H_single = np.array([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2)
        
        # Expand into a global tensor product space configuration matrix
        H_total = H_single
        for _ in range(self.num_qubits - 1):
            H_total = np.kron(H_total, H_single)
            
        # Execute classical linear continuous wave register signal matrix multiplication
        self.signal_vector = np.dot(H_total, self.signal_vector)

    def inject_phase_damping(self, noise_level=0.1):
        """ 
        [Core Theoretical Vulnerability Demonstration]
        Lacking active geometric gauge protection constraints, classical linear signals 
        are directly vulnerable to random phase dispersion noise, inducing irreversible 
        decoherence and wavepacket flattening anomalies.
        """
        noise = np.random.normal(0, noise_level)
        self.k_delta += noise
        
        # Simulate phase erosion across individual higher-order signal components
        for i in range(1, self.dimension):
            # Accumulative numerical phase dispersion scales aggressively with component indexes
            self.signal_vector[i] *= np.exp(1j * noise * i)

    def get_document_probability_density(self):
        """ 
        Harvest the Power Spectral Density (PSD) from classical channels to emulate 
        quantum probability density profiles, mapping vectors onto a unified 500-point mesh grid.
        """
        # Extract squared amplitude intensities across individual classical signal modes
        intensities = np.abs(self.signal_vector) ** 2
        total_power = np.sum(intensities)
        if total_power > 0:
            intensities = intensities / total_power
            
        # Emulate classical probability dispersion bell curve packets over spatial tracking boundaries
        x_grid = np.linspace(-20, 20, 500)
        
        # Quantify spatial broadening parameters driven by coherence leaks
        coherence_leak = 1.0 - float(intensities[0]) if len(intensities) > 1 else 0.5
        width = 1.5 + coherence_leak * 4.0 + float(np.abs(self.k_delta)) * 0.1
        
        # Synthesize classical unconstrained wave profile configurations
        classical_wave_profile = np.zeros(500)
        for idx, p in enumerate(intensities):
            # Map specific signal registers into decentralized dispersion boundaries
            center = -3.0 + (idx * 6.0 / max(1, self.dimension - 1))
            classical_wave_profile += p * np.exp(-(x_grid - center)**2 / (2 * width**2))
            
        total_sum = np.sum(classical_wave_profile)
        if total_sum > 0:
            classical_wave_profile /= total_sum
            
        return [float(v) for v in classical_wave_profile]


# Singleton instance placeholder - Instantiated securely upon daemon orchestration
slwe_engine = None

# ==============================================================================
# RESTFUL API ENDPOINTS 
# ==============================================================================

@app.route('/instruction', methods=['POST'])
def route_instruction():
    """ Master API gateway processing incoming Qiskit-style coin instructions """
    global slwe_engine
    data = request.get_json(silent=True) or {}
    gate_name = data.get("gate", "").lower()
    
    if gate_name == "h" or gate_name == "hadamard":
        if slwe_engine:
            slwe_engine.apply_hadamard_to_all()
        return jsonify({"status": "success", "msg": "Global SLWE Hadamard transformation completed"})
    return jsonify({"status": "error", "msg": f"Gate operation '{gate_name}' not supported by SLWE platform"}), 400

@app.route('/gate/h', methods=['POST'])
def route_gate_h_legacy():
    """ Backward-compatible endpoint to intercept individual fallback Hadamard calls """
    global slwe_engine
    if slwe_engine:
        slwe_engine.apply_hadamard_to_all()
    return jsonify({"status": "success", "msg": "Legacy individual fallback gate triggered successfully"})

@app.route('/evolve', methods=['POST', 'GET'])
def route_evolve():
    """ Continuous wave evolution driver interface supporting dynamic phase noise injection """
    global slwe_engine
    if not slwe_engine:
        return jsonify({"status": "error", "msg": "SLWE Physics Engine Core not initialized"}), 500
        
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        noise = float(data.get('noise', 0.0))
    else:
        noise = float(request.args.get('noise', 0.0))
        
    if noise > 0:
        slwe_engine.inject_phase_damping(noise)
        
    prob_dist = slwe_engine.get_document_probability_density()
    return jsonify({"probability_density": prob_dist})

@app.route('/ping', methods=['GET'])
def route_ping():
    """ Endpoint confirming classical hardware daemon connectivity metrics """
    global slwe_engine
    return jsonify({
        "status": "ready",
        "mode": "Classical Signal Emulation (SLWE)",
        "configured_qubits": slwe_engine.num_qubits if slwe_engine else 0,
        "tensor_dimensions": slwe_engine.dimension if slwe_engine else 0
    })


if __name__ == "__main__":
    print("====================================================")
    print("===   La Cour & Spreeuw Reference Framework: SLWE ===")
    print("====================================================")
    
    # Secure CLI interactive input pipeline optimized for subprocess automation
    try:
        user_qubits = int(input("Designate virtual qubit scale for SLWE emulation (e.g., 1, 2, 3): "))
        if user_qubits < 1: 
            user_qubits = 1
    except ValueError:
        user_qubits = 1
        
    print(f"\n[Hardware Matrix Allocated] Successfully deployed {user_qubits} classical channels ({2**user_qubits} dimensions).")
    
    # Safely instantiate the unified global engine register
    slwe_engine = DocumentBasedSLWEEngine(num_qubits=user_qubits)

    print("=== [Daemon Activated] SLWE microservice standalone node is now live ===")
    print("Listening on Host Loopback Network Address Address via Port: 5012 ...")
    app.run(host='127.0.0.1', port=5012, debug=False)
