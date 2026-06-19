# ==============================================================================
# CLASSICAL SIGNAL-BASED LINEAR WAVE EQUATION (SLWE) BENCHMARK NODE
# ==============================================================================

import numpy as np
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

class DocumentBasedSLWEEngine:
    def __init__(self, num_qubits=1):
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits  
        self.signal_vector = np.zeros(self.dimension, dtype=complex)
        self.signal_vector[0] = 1.0 + 0j
        self.current_step = 0
        self.k_delta = 0.0

    def apply_hadamard_to_all(self):
        H_single = np.array([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2)
        H_total = H_single
        for _ in range(self.num_qubits - 1):
            H_total = np.kron(H_total, H_single)
        self.signal_vector = np.dot(H_total, self.signal_vector)
        self._enforce_normalization_safeguard()

    def apply_phase_rotation_to_all(self, delta_phi):
        for i in range(1, self.dimension):
            self.signal_vector[i] *= np.exp(1j * delta_phi * i)
        self._enforce_normalization_safeguard()

    def inject_phase_damping(self, noise_level=0.1):
        noise = np.random.normal(0, noise_level)
        self.k_delta += noise
        for i in range(1, self.dimension):
            self.signal_vector[i] *= np.exp(1j * noise * i)
        self._enforce_normalization_safeguard()

    def _enforce_normalization_safeguard(self):
        total_power = np.sum(np.abs(self.signal_vector) ** 2)
        if total_power > 0:
            self.signal_vector = self.signal_vector / np.sqrt(total_power)

    def get_document_probability_density(self):
        intensities = np.abs(self.signal_vector) ** 2
        x_grid = np.linspace(-20, 20, 500)
        coherence_leak = 1.0 - float(intensities[0]) if len(intensities) > 1 else 0.5
        width = 1.5 + coherence_leak * 2.0 + float(np.abs(self.k_delta)) * 0.05
        
        classical_wave_profile = np.zeros(500)
        for idx, p in enumerate(intensities):
            center = -3.0 + (idx * 6.0 / max(1, self.dimension - 1))
            classical_wave_profile += p * np.exp(-(x_grid - center)**2 / (2 * width**2))
            
        total_sum = np.sum(classical_wave_profile)
        if total_sum > 0:
            classical_wave_profile /= total_sum
        return [float(v) for v in classical_wave_profile]

slwe_engine = None

@app.route('/reset', methods=['POST'])
def route_reset():
    global slwe_engine
    if slwe_engine:
        slwe_engine.signal_vector = np.zeros(slwe_engine.dimension, dtype=complex)
        slwe_engine.signal_vector[0] = 1.0 + 0j
        slwe_engine.k_delta = 0.0
    return jsonify({"status": "success", "msg": "SLWE engine state reset successfully"})

@app.route('/instruction', methods=['POST'])
def route_instruction():
    global slwe_engine
    data = request.get_json(silent=True) or {}
    gate_name = data.get("gate", "").lower()
    
    if gate_name in ["h", "hadamard"]:
        if slwe_engine: slwe_engine.apply_hadamard_to_all()
        return jsonify({"status": "success", "msg": "Global SLWE Hadamard completed"})
    elif gate_name in ["phase", "p"]:
        delta_phi = float(data.get("delta_phi", 0.0))
        if slwe_engine: slwe_engine.apply_phase_rotation_to_all(delta_phi)
        return jsonify({"status": "success", "msg": "Global SLWE Phase rotation completed"})
    elif gate_name in ["x", "not"]:
        if slwe_engine: slwe_engine.signal_vector = np.flip(slwe_engine.signal_vector)
        return jsonify({"status": "success", "msg": "Global SLWE Bit-flip executed"})
    return jsonify({"status": "error", "msg": f"Gate operation '{gate_name}' not supported"}), 400

@app.route('/evolve', methods=['POST', 'GET'])
def route_evolve():
    global slwe_engine
    if not slwe_engine: return jsonify({"status": "error", "msg": "Core not initialized"}), 500
    data = request.get_json(silent=True) or {} if request.method == 'POST' else request.args
    noise = float(data.get('noise', 0.0))
    if noise > 0: slwe_engine.inject_phase_damping(noise)
    prob_dist = slwe_engine.get_document_probability_density()
    return jsonify({"probability_density": prob_dist, "gauge_metric_integrity": float(np.abs(slwe_engine.signal_vector[0]) ** 2)})

if __name__ == "__main__":
    try:
        user_qubits = int(os.environ.get("SLWE_QUBITS_SCALE", "1"))
    except ValueError:
        user_qubits = 1
    slwe_engine = DocumentBasedSLWEEngine(num_qubits=user_qubits)
    app.run(host='127.0.0.1', port=6000, debug=False, threaded=True)
