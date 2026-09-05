# ==============================================================================
# HILBERT SPACE SPINOR QUASIPARTICLE (HSQ) QUANTUM EMULATOR NODE [VERSION 5.1]
# [REDIS PUB/SUB BROADCAST ENGINE & NATIVE ATOMIC CNOT-PHASE MERGED GATE]
# Dynamic Host Configuration Support (No Hardcoded IP)
# ==============================================================================

import os
import sys
import time
import json
import platform
import threading
import hashlib
from typing import Optional, List
import numpy as np
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# --- 🚀 Hardware Acceleration Check (GPU/CPU) ---
try:
    import cupy as cp
    xp = cp
    HAS_GPU = True
except ImportError:
    xp = np
    HAS_GPU = False

app = FastAPI(title="HSQ Quantum Emulator Node")
simulation_lock = threading.Lock()

# --- 🌐 Central Interlock Redis Tensor Switch Connection (動態環境變數) ---
TENSOR_BUS_HOST = os.environ.get("TENSOR_BUS_HOST", "localhost")
TENSOR_BUS_PORT = int(os.environ.get("TENSOR_BUS_PORT", 2057))
NODE_PORT = int(os.environ.get("NODE_PORT", 5000))

try:
    tensor_bus = redis.Redis(
        host=TENSOR_BUS_HOST, 
        port=TENSOR_BUS_PORT, 
        db=0, 
        decode_responses=True, 
        socket_timeout=1.0
    )
    tensor_bus.ping()
    BUS_CONNECTED = True
    print(f"🔗 [Tensor Bus] Bound to Virtual Switch at {TENSOR_BUS_HOST}:{TENSOR_BUS_PORT}")
except redis.ConnectionError:
    tensor_bus = None
    BUS_CONNECTED = False
    print(f"⚠️ [Tensor Bus] Virtual Switch not detected at {TENSOR_BUS_HOST}:{TENSOR_BUS_PORT}. Operating in isolated mode.")


class HilbertSpaceSpinorQuasiparticleService:
    def __init__(self):
        self.reset_to_vacuum()

    def reset_to_vacuum(self):
        """ Reset qubit to pure vacuum ground state |0> """
        self.omega_0 = 2.0  
        self.k_L = 1.2
        self.k_R = -1.2
        self.sigma = 2.0    
        self.vg = 0.8       
        self.alpha = 0.0    
        self.current_step = 0
        self.a = 1.0 + 0j   # Ground State |0>
        self.b = 0.0 + 0j   # Excited State |1>
        self.theta = 0.0
        self.phi = 0.0
        self.k_delta = 0.0  
        self.t_accumulated = 0.0

    def enforce_gauge_protection(self):
        """ Enforces strict complex-field normalization to guarantee unitary safety. """
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

    def apply_cnot_and_phase_gate(self, c_a0: complex, c_b0: complex, delta_phi: float = 0.0):
        """ 🌟 原子合體閘：一次性完成 CNOT 複數編織與 Phase 相位注入 (解決 Stage 3 卡頓) """
        new_a1 = c_a0 * self.a + c_b0 * self.b
        new_b1 = c_a0 * self.b + c_b0 * self.a
        self.a, self.b = new_a1, new_b1

        if delta_phi != 0.0:
            self.phi = delta_phi
            self.b = self.b * np.exp(1j * delta_phi)

        self.enforce_gauge_protection()

    def inject_phase_damping(self, noise_level=0.1, seed_val=None):
        if noise_level <= 0.0:
            return
            
        if seed_val is not None:
            entropy_pool = f"{seed_val}_{self.current_step}_{platform.node()}"
            hash_bytes = hashlib.sha256(entropy_pool.encode('utf-8')).digest()
            actual_seed = int.from_bytes(hash_bytes[:4], byteorder='big')
        else:
            actual_seed = time.time_ns() & 0xFFFFFFFF
            
        rng = np.random.default_rng(actual_seed)
        noise = rng.normal(0, noise_level)
        
        self.k_delta += noise  
        self.b = self.b * np.exp(1j * noise)
        self.enforce_gauge_protection()

    def compute_current_xi(self, grid_size: int = 500):
        t = self.t_accumulated
        x_grid = xp.linspace(-20, 20, grid_size)
        
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


# --- 📡 Redis Pub/Sub 背景廣播監聽器 ---
def start_redis_pubsub_listener():
    """ 訂閱 Redis Channel，接收 Pub/Sub 零延遲廣播指令 """
    if not BUS_CONNECTED:
        return

    pubsub = tensor_bus.pubsub()
    node_channel = f"hsq_channel_{NODE_PORT}"
    global_channel = "hsq_global_channel"
    
    pubsub.subscribe(node_channel, global_channel)
    print(f"📡 [Pub/Sub Listener] Active on '{node_channel}' & '{global_channel}'")

    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                payload = json.loads(message["data"])
                action = payload.get("action")

                if action == "reset":
                    with simulation_lock:
                        hsq_qubit.reset_to_vacuum()

                elif action == "instruction":
                    gate_name = payload.get("gate", "").lower()
                    
                    if gate_name == "cnot_and_phase":
                        source_key = payload.get("source_bus_key")
                        delta_phi = float(payload.get("delta_phi", 0.0))
                        control_raw = tensor_bus.get(source_key)
                        
                        if control_raw:
                            parts = control_raw.split(",")
                            c_a0 = complex(float(parts[0]), float(parts[1]))
                            c_b0 = complex(float(parts[2]), float(parts[3]))
                            
                            with simulation_lock:
                                hsq_qubit.apply_cnot_and_phase_gate(c_a0, c_b0, delta_phi)

                    elif gate_name in ["h", "hadamard"]:
                        with simulation_lock:
                            hsq_qubit.apply_hadamard_gate()

                    elif gate_name in ["x", "not"]:
                        with simulation_lock:
                            hsq_qubit.apply_pauli_x_gate()

                elif action == "evolve":
                    dt = float(payload.get("dt", 0.1))
                    noise = float(payload.get("noise", 0.0))
                    with simulation_lock:
                        hsq_qubit.current_step += 1
                        hsq_qubit.t_accumulated += dt
                        hsq_qubit.inject_phase_damping(noise)

            except Exception as e:
                print(f"⚠️ [Pub/Sub Exception] {e}")

# 啟動 Pub/Sub 背景執行緒
if BUS_CONNECTED:
    listener_thread = threading.Thread(target=start_redis_pubsub_listener, daemon=True)
    listener_thread.start()


# --- 📋 FastAPI Schemas & Endpoints ---
class InstructionPayload(BaseModel):
    gate: str
    delta_phi: float = 0.0
    bus_key: Optional[str] = None
    source_bus_key: Optional[str] = None

class EvolvePayload(BaseModel):
    noise: float = 0.0
    seed: Optional[int] = None
    t: Optional[float] = None
    grid_size: Optional[int] = 500  


@app.post("/instruction")
def route_instruction(payload: InstructionPayload):
    gate_name = payload.gate.lower()

    if gate_name == "export_tensor_metric":
        if not payload.bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing bus_key or Tensor Bus disconnected")
        with simulation_lock:
            state_a_real, state_a_imag = float(hsq_qubit.a.real), float(hsq_qubit.a.imag)
            state_b_real, state_b_imag = float(hsq_qubit.b.real), float(hsq_qubit.b.imag)
            
        try:
            payload_str = f"{state_a_real},{state_a_imag},{state_b_real},{state_b_imag}"
            tensor_bus.set(payload.bus_key, payload_str)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus write failure: {e}")
        return {
            "status": "success", 
            "gate": "export HSQ coin amplitudes (a,b) to Redis", 
            "state_a": [state_a_real, state_a_imag],
            "state_b": [state_b_real, state_b_imag]
        }

    elif gate_name in ["cnot_and_phase", "cnot_phase_interlock"]:
        if not payload.source_bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing source_bus_key or Tensor Bus disconnected")
        try:
            control_raw_str = tensor_bus.get(payload.source_bus_key)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus read failure: {e}")

        if control_raw_str is None:
            raise HTTPException(status_code=404, detail=f"Metric '{payload.source_bus_key}' not found on Tensor Bus")

        parts = control_raw_str.split(",")
        c_a0 = complex(float(parts[0]), float(parts[1]))
        c_b0 = complex(float(parts[2]), float(parts[3]))

        with simulation_lock:
            hsq_qubit.apply_cnot_and_phase_gate(c_a0, c_b0, payload.delta_phi)

        return {"status": "success", "gate": "ATOMIC CNOT AND PHASE INTERLOCK"}

    with simulation_lock:
        if gate_name in ["h", "hadamard"]:
            hsq_qubit.apply_hadamard_gate()
        elif gate_name in ["x", "not"]:
            hsq_qubit.apply_pauli_x_gate()
        elif gate_name in ["phase", "p"]:
            hsq_qubit.apply_phase_rotation_gate(payload.delta_phi)
        else:
            raise HTTPException(status_code=400, detail=f"Gate instruction '{gate_name}' not natively supported")
            
        return {
            "status": "success",
            "gate": gate_name.upper(),
            "statevector": [
                {"real": float(hsq_qubit.a.real), "imag": float(hsq_qubit.a.imag)},
                {"real": float(hsq_qubit.b.real), "imag": float(hsq_qubit.b.imag)}
            ]
        }


@app.post("/evolve")
def route_evolve(payload: EvolvePayload):
    with simulation_lock:
        hsq_qubit.current_step += 1
        dt = float(payload.t) if payload.t is not None else 0.1
        hsq_qubit.t_accumulated += dt

        active_grid = payload.grid_size if payload.grid_size and payload.grid_size > 0 else 500
        
        hsq_qubit.inject_phase_damping(payload.noise, seed_val=payload.seed)
        prob_dist = hsq_qubit.compute_current_xi(grid_size=active_grid)
        integrity = float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2)
    return {
        "status": "evolved",
        "t_final": hsq_qubit.t_accumulated,
        "gauge_metric_integrity": integrity,
        "probability_density": prob_dist,
        "active_hilbert_grid_samples": active_grid  
    }


@app.get("/ping")
def route_ping():
    return {
        "status": "ready",
        "device": "NVIDIA GPU Simulation Mode" if HAS_GPU else "CPU Simulation Mode",
        "cuda_accelerated": HAS_GPU,
        "tensor_bus_active": BUS_CONNECTED,
        "node_port": NODE_PORT
    }


@app.post("/reset")
def route_reset():
    with simulation_lock:
        hsq_qubit.reset_to_vacuum()
    return {"status": "success", "msg": "HSQ qubit register vacuum-reset successfully"}


if __name__ == "__main__":
    # 支援啟動時從命令列參數輸入 Port（例如：python hsq_node.py 5011）
    NODE_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else NODE_PORT
    uvicorn.run(app, host="0.0.0.0", port=NODE_PORT)
