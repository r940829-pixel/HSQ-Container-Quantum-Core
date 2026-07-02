# ==============================================================================
# HILBERT-SPACE SPINOR QUASIPARTICLE (HSQ) COMPUTATIONAL MICROSERVICE
# [FINAL PRODUCTION READY - 100% CLOSED LOOP]
# Fully optimized for multi-node high-frequency scholastic simulations.
# ==============================================================================

import platform
import time
import os
import threading
import numpy as np
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

try:
    import cupy as cp
    xp = cp
    HAS_GPU = True
except ImportError:
    xp = np
    HAS_GPU = False

app = FastAPI(title="HSQ Quantum Emulator Node")
simulation_lock = threading.Lock()

TENSOR_BUS_HOST = os.environ.get("TENSOR_BUS_HOST", "localhost")
try:
    tensor_bus = redis.Redis(host=TENSOR_BUS_HOST, port=2057, db=0, decode_responses=True, socket_timeout=1.0)
    tensor_bus.ping()
    BUS_CONNECTED = True
    print(f"🔗 [Tensor Bus] Bound to Virtual Switch at {TENSOR_BUS_HOST}:2057")
except redis.ConnectionError:
    tensor_bus = None
    BUS_CONNECTED = False
    print("⚠️ [Tensor Bus] Virtual Switch not detected. Operating in isolated mode.")

class HilbertSpaceSpinorQuasiparticleService:
    def __init__(self):
        self.reset_to_vacuum()

    def reset_to_vacuum(self):
        self.omega_0 = 2.0  
        self.k_L = 1.2
        self.k_R = -1.2
        self.sigma = 2.0    
        self.vg = 0.8       
        self.alpha = 0.1    
        self.current_step = 0
        self.a = 1.0 + 0j
        self.b = 0.0 + 0j
        self.theta = 0.0
        self.phi = 0.0
        self.k_delta = 0.0  

    def enforce_gauge_protection(self):
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
        if noise_level <= 0.0:
            self.k_delta = 0.0  
            return
        machine_name = platform.node() or os.environ.get("HOSTNAME", "GPU_NODE_PROD")
        char_sum = sum(ord(c) for c in machine_name)
        nanosecond_entropy = time.time_ns()
        if seed_val is not None:
            time_mask = (nanosecond_entropy + int(self.current_step)) % (2**32 - 1)
            actual_seed = (int(seed_val) ^ time_mask) * 31 + char_sum
        else:
            actual_seed = nanosecond_entropy + char_sum
        actual_seed = abs(actual_seed) % (2**32 - 1)
        rng = np.random.default_rng(actual_seed)
        noise = rng.normal(0, noise_level)
        self.k_delta += noise  
        self.b = self.b * np.exp(1j * noise)
        self.enforce_gauge_protection()

    def compute_current_xi(self, t=1.0):
        x_grid = xp.linspace(-20, 20, 500)
        current_sigma = np.sqrt(self.sigma**2 + self.alpha * t)
        envelope_a = xp.exp(-((x_grid + self.vg * t)**2) / (2 * current_sigma**2))
        envelope_b = xp.exp(-((x_grid - self.vg * t)**2) / (2 * current_sigma**2))
        time_phase = self.omega_0 * t
        phase_L = (self.k_L - self.k_delta) * x_grid + time_phase
        phase_R = (self.k_R - self.k_delta) * x_grid + time_phase + self.phi
        xi_total = self.a * envelope_a * xp.exp(1j * phase_L) + self.b * envelope_b * xp.exp(1j * phase_R)
        prob = xp.abs(xi_total)**2
        total_sum = float(xp.sum(prob))
        if total_sum > 0:
            prob = prob / total_sum
        if HAS_GPU:
            result = cp.asnumpy(prob).astype(float).tolist()
            cp.get_default_memory_pool().free_all_blocks()  
            return result
        return prob.astype(float).tolist()

hsq_qubit = HilbertSpaceSpinorQuasiparticleService()

class InstructionPayload(BaseModel):
    gate: str
    delta_phi: float = 0.0
    bus_key: Optional[str] = None
    source_bus_key: Optional[str] = None

class EvolvePayload(BaseModel):
    noise: float = 0.0
    seed: Optional[int] = None
    t: Optional[float] = None

@app.post("/instruction")
def route_instruction(payload: InstructionPayload):
    gate_name = payload.gate.lower()
    
    if gate_name == "export_tensor_metric":
        if not payload.bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing bus_key or Tensor Bus disconnected")
        with simulation_lock:
            relative_phase = float(np.angle(hsq_qubit.a) - np.angle(hsq_qubit.b))
        try:
            tensor_bus.set(payload.bus_key, str(relative_phase))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus write failure: {e}")
        return {"status": "success", "gate": "Export Spinor Phase Metric", "exported_metric": relative_phase}

    elif gate_name == "apply_conditional_phase":
        if not payload.source_bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing source_bus_key or Tensor Bus disconnected")
        try:
            control_metric_str = tensor_bus.get(payload.source_bus_key)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus read failure: {e}")
            
        if control_metric_str is None:
            raise HTTPException(status_code=404, detail=f"Metric {payload.source_bus_key} not found on Tensor Bus")
        
        source_phase = float(control_metric_str)
        with simulation_lock:
            true_unitary_phase = payload.delta_phi * np.cos(source_phase)
            hsq_qubit.apply_phase_rotation_gate(true_unitary_phase)
            a_mag, b_mag = float(np.abs(hsq_qubit.a)), float(np.abs(hsq_qubit.b))
            
        return {
            "status": "success", 
            "gate": "Conditional Unitary Phase Intersection",
            "control_source_phase": source_phase,
            "applied_phase_shift": true_unitary_phase,
            "a_magnitude": a_mag, 
            "b_magnitude": b_mag
        }

    with simulation_lock:
        if gate_name in ["h", "hadamard"]:
            hsq_qubit.apply_hadamard_gate()
            return {"status": "success", "gate": "Hadamard", "a_magnitude": float(np.abs(hsq_qubit.a)), "b_magnitude": float(np.abs(hsq_qubit.b))}
        elif gate_name in ["x", "not"]:
            hsq_qubit.apply_pauli_x_gate()
            return {"status": "success", "gate": "Pauli-X", "a_magnitude": float(np.abs(hsq_qubit.a)), "b_magnitude": float(np.abs(hsq_qubit.b))}
        elif gate_name in ["phase", "p"]:
            hsq_qubit.apply_phase_rotation_gate(payload.delta_phi)
            return {"status": "success", "gate": "Phase Rotation", "phi": float(hsq_qubit.phi)}
            
    raise HTTPException(status_code=400, detail=f"Gate instruction '{gate_name}' not natively supported")

@app.post("/evolve")
def route_evolve(payload: EvolvePayload):
    with simulation_lock:
        hsq_qubit.current_step += 1
        t = float(payload.t) if payload.t is not None else hsq_qubit.current_step * 0.1
        hsq_qubit.inject_phase_damping(payload.noise, seed_val=payload.seed)
        prob_dist = hsq_qubit.compute_current_xi(t=t)
        integrity = float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2)
    return {
        "status": "evolved",
        "t_final": t,
        "gauge_metric_integrity": integrity,
        "probability_density": prob_dist
    }

@app.get("/ping")
def route_ping():
    return {
        "status": "ready",
        "device": "NVIDIA GPU Hardware Acceleration Direct Access Mode" if HAS_GPU else "CPU Simulation Mode",
        "cuda_accelerated": HAS_GPU,
        "tensor_bus_active": BUS_CONNECTED
    }

@app.post("/reset")
def route_reset():
    with simulation_lock:
        hsq_qubit.reset_to_vacuum()
    return {"status": "success", "msg": "HSQ qubit register vacuum-reset successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
