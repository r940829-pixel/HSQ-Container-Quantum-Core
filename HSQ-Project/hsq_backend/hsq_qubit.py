# ==============================================================================
# HILBERT SPACE SPINOR QUASIPARTICLE (HSQ) QUANTUM EMULATOR NODE [VERSION 7.0]
# [THE FINAL PUZZLE - COMPLETE UNIVERSAL TENSOR SET ENABLED]
# Supports Single: H, X, Y, Z, S, T, Rx, Ry, Rz, Phase, U
# Supports 2-Qubit: CNOT, CPhase, Phase-Sync, SWAP, CH, CY, CZ, CS, CT, CRx, CRy, CRz, CU, CSync_phase
# Supports 3-Qubit: CCNOT (Toffoli), CSWAP (Fredkin)
# Optimized with O(N) Redis Memory Footprint & Non-Local Phase Chain Interlock.
# ==============================================================================

import os
import sys
import time
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

app = FastAPI(title="HSQ Quantum Emulator Node - Version 7.0 (Complete Universal Tensor Set)")
simulation_lock = threading.Lock()

# --- 🌐 Central Interlock Redis Tensor Switch Connection ---
TENSOR_BUS_HOST = os.environ.get("TENSOR_BUS_HOST", "localhost")
TENSOR_BUS_PORT = int(os.environ.get("TENSOR_BUS_PORT", 2057))

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
    print(f"🔗 [Tensor Bus] Interlocked into Central Switch at {TENSOR_BUS_HOST}:{TENSOR_BUS_PORT}")
except redis.ConnectionError:
    tensor_bus = None
    BUS_CONNECTED = False
    print("⚠️ [Tensor Bus] Virtual Switch offline. Operating in isolated node mode.")


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

        # 🌟 拓樸相位鏈記憶體 (Topological Phase Chain Memory)
        self.phase_chain_factor = 1.0 + 0j

        self.theta = 0.0
        self.phi = 0.0
        self.k_delta = 0.0  
        self.t_accumulated = 0.0

    def enforce_gauge_protection(self):
        """ Strict complex-field normalization (|a|^2 + |b|^2 = 1.0) """
        norm = np.sqrt(np.abs(self.a)**2 + np.abs(self.b)**2)
        if norm > 1e-15:
            self.a /= norm
            self.b /= norm
        # 規範化相位因子
        chain_norm = np.abs(self.phase_chain_factor)
        if chain_norm > 1e-15:
            self.phase_chain_factor /= chain_norm

    # ==============================================================
    # 🌟 UNIVERSAL QUANTUM GATE SET (通用量子邏輯閘實作)
    # ==============================================================

    def apply_u_gate(self, theta, phi, lam):
        """ 萬用單量子閘 U(theta, phi, lambda) """
        op_a = self.a * np.cos(theta/2) - self.b * np.exp(1j * lam) * np.sin(theta/2)
        op_b = self.a * np.exp(1j * phi) * np.sin(theta/2) + self.b * np.exp(1j * (phi + lam)) * np.cos(theta/2)
        self.a, self.b = op_a, op_b
        self.enforce_gauge_protection()

    def apply_hadamard_gate(self):
        new_a = (1.0 / np.sqrt(2)) * (self.a + self.b)
        new_b = (1.0 / np.sqrt(2)) * (self.a - self.b)
        self.a, self.b = new_a, new_b
        self.enforce_gauge_protection()

    def apply_pauli_x_gate(self):
        self.a, self.b = self.b, self.a
        self.enforce_gauge_protection()

    def apply_pauli_y_gate(self):
        new_a = -1j * self.b
        new_b = 1j * self.a
        self.a, self.b = new_a, new_b
        self.phase_chain_factor *= -1j
        self.enforce_gauge_protection()

    def apply_pauli_z_gate(self):
        self.b = -self.b
        self.phase_chain_factor *= -1.0
        self.enforce_gauge_protection()

    def apply_s_gate(self):
        self.b = 1j * self.b
        self.phase_chain_factor *= 1j
        self.enforce_gauge_protection()

    def apply_t_gate(self):
        phase_factor = np.exp(1j * np.pi / 4.0)
        self.b = phase_factor * self.b
        self.phase_chain_factor *= phase_factor
        self.enforce_gauge_protection()

    def apply_phase_rotation_gate(self, delta_phi):
        phase_factor = np.exp(1j * delta_phi)
        self.phi += delta_phi
        self.b = self.b * phase_factor
        self.phase_chain_factor *= phase_factor
        self.enforce_gauge_protection()

    def apply_rx_gate(self, theta):
        new_a = self.a * np.cos(theta/2) - 1j * self.b * np.sin(theta/2)
        new_b = -1j * self.a * np.sin(theta/2) + self.b * np.cos(theta/2)
        self.a, self.b = new_a, new_b
        self.enforce_gauge_protection()

    def apply_ry_gate(self, theta):
        new_a = self.a * np.cos(theta/2) - self.b * np.sin(theta/2)
        new_b = self.a * np.sin(theta/2) + self.b * np.cos(theta/2)
        self.a, self.b = new_a, new_b
        self.enforce_gauge_protection()

    def apply_rz_gate(self, theta):
        self.a = self.a * np.exp(-1j * theta/2)
        self.b = self.b * np.exp(1j * theta/2)
        self.phase_chain_factor *= np.exp(1j * theta/2)
        self.enforce_gauge_protection()

    def inject_phase_damping(self, noise_level=0.1, seed_val=None):
        if noise_level <= 0.0: return
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
        if total_sum > 0: prob = prob / total_sum

        if HAS_GPU:
            result = cp.asnumpy(prob).astype(float).tolist()
            cp.get_default_memory_pool().free_all_blocks()  
            return result
        return prob.astype(float).tolist()


hsq_qubit = HilbertSpaceSpinorQuasiparticleService()

class InstructionPayload(BaseModel):
    gate: str
    delta_phi: float = 0.0          # Maps to theta for U/CU gates
    phi_angle: float = 0.0          # Maps to phi for U/CU gates
    lambda_angle: float = 0.0       # Maps to lambda for U/CU gates
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

    # 1. 導出狀態與拓樸相位鏈
    if gate_name == "export_tensor_metric":
        if not payload.bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing bus_key or Tensor Bus disconnected")

        with simulation_lock:
            a_r, a_i = float(hsq_qubit.a.real), float(hsq_qubit.a.imag)
            b_r, b_i = float(hsq_qubit.b.real), float(hsq_qubit.b.imag)
            c_r, c_i = float(hsq_qubit.phase_chain_factor.real), float(hsq_qubit.phase_chain_factor.imag)
            step = hsq_qubit.current_step

        try:
            payload_str = f"{a_r},{a_i},{b_r},{b_i},{step},{c_r},{c_i}"
            tensor_bus.set(payload.bus_key, payload_str)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus write failure: {e}")

        return {
            "status": "success", 
            "gate": "Export Spinor & Phase Chain to Tensor Bus", 
            "state_a": [a_r, a_i],
            "state_b": [b_r, b_i],
            "phase_chain": [c_r, c_i]
        }

    # 🌟 2. 拓樸相位鏈同步與 Y 基底投影對齊
    elif gate_name in ["sync_phase_chain", "sync_phase"]:
        if not payload.source_bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing source_bus_key")

        source_keys = [k.strip() for k in payload.source_bus_key.split(",") if k.strip()]
        try:
            raw_states = tensor_bus.mget(source_keys)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus MGET failure: {e}")

        total_remote_phase = 1.0 + 0j
        valid_count = 0
        for idx, raw_str in enumerate(raw_states):
            if raw_str is None: continue
            parts = raw_str.split(",")
            if len(parts) >= 7:
                c_phase = complex(float(parts[5]), float(parts[6]))
                if np.abs(c_phase) > 1e-15:
                    total_remote_phase *= c_phase
                    valid_count += 1

        if valid_count > 0:
            with simulation_lock:
                phase_angle = np.angle(total_remote_phase)
                if abs(phase_angle) > 1e-5:
                    hsq_qubit.a, hsq_qubit.b = hsq_qubit.b, -hsq_qubit.a
                    hsq_qubit.phi += np.pi  
                    hsq_qubit.enforce_gauge_protection()

        return {"status": "success", "gate": "RELATIVE PHASE CHAIN SYNC"}

    # 🚀 3. 三體高階糾纏閘 (3-Qubit Interlock: CCNOT, CSWAP)
    elif gate_name in ["ccnot", "toffoli", "cswap", "fredkin"]:
        if not payload.source_bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing source_bus_key")
            
        source_keys = [k.strip() for k in payload.source_bus_key.split(",") if k.strip()]
        if len(source_keys) < 2:
            raise HTTPException(status_code=400, detail="CCNOT/CSWAP requires exactly 2 remote tensor keys")
            
        try:
            raw_states = tensor_bus.mget(source_keys[:2])
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus failure: {e}")
            
        node1 = raw_states[0].split(",") if raw_states[0] else None
        node2 = raw_states[1].split(",") if raw_states[1] else None
        
        if not node1 or not node2:
            raise HTTPException(status_code=502, detail="Incomplete remote tensor data for 3-qubit gate")

        # 控制節點 1 的狀態
        c1_0 = complex(float(node1[0]), float(node1[1]))
        c1_1 = complex(float(node1[2]), float(node1[3]))
        # 控制/目標節點 2 的狀態
        c2_0 = complex(float(node2[0]), float(node2[1]))
        c2_1 = complex(float(node2[2]), float(node2[3]))

        with simulation_lock:
            a, b = hsq_qubit.a, hsq_qubit.b
            
            if gate_name in ["ccnot", "toffoli"]:
                # 只有當兩個 Control 都是 |1> 時才翻轉
                c_11 = c1_1 * c2_1
                c_rest = c1_0 * c2_0 + c1_0 * c2_1 + c1_1 * c2_0
                
                hsq_qubit.a = c_rest * a + c_11 * b
                hsq_qubit.b = c_rest * b + c_11 * a
                
                remote_phase = 1.0 + 0j
                if len(node1) >= 7: remote_phase *= complex(float(node1[5]), float(node1[6]))
                if len(node2) >= 7: remote_phase *= complex(float(node2[5]), float(node2[6]))
                p_11 = np.abs(c_11)**2
                hsq_qubit.phase_chain_factor *= (remote_phase * p_11 + 1.0 * (1 - p_11))

            elif gate_name in ["cswap", "fredkin"]:
                # node1 = Control, node2 = Target2. 若 Control=|1>，本節點與 Target2 狀態交換
                hsq_qubit.a = c1_0 * a + c1_1 * c2_0
                hsq_qubit.b = c1_0 * b + c1_1 * c2_1
                
                remote_phase = 1.0 + 0j
                if len(node1) >= 7: remote_phase *= complex(float(node1[5]), float(node1[6]))
                if len(node2) >= 7: remote_phase *= complex(float(node2[5]), float(node2[6]))
                hsq_qubit.phase_chain_factor *= (remote_phase * np.abs(c1_1)**2 + 1.0 * np.abs(c1_0)**2)
                
            hsq_qubit.enforce_gauge_protection()

        return {"status": "success", "gate": gate_name.upper() + " INTERLOCK"}

    # 🚀 4. 多體與受控雙量子閘 (2-Qubit Interlock: CNOT, CPhase, CH, CU, SWAP, etc.)
    elif gate_name in ["multi_tensor_interlock", "tensor_product", "cnot_interlock", "bell", "cnot",
                       "cphase", "controlled_phase", "cr", "ch", "cy", "cz", "cs", "ct", "crx", "cry", "crz", "cu", "swap", "csync_phase"]:
        if not payload.source_bus_key or not BUS_CONNECTED:
            raise HTTPException(status_code=400, detail="Missing source_bus_key")

        source_keys = [k.strip() for k in payload.source_bus_key.split(",") if k.strip()]
        try:
            raw_states = tensor_bus.mget(source_keys)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Tensor Bus failure: {e}")

        c_zero, c_one = 1.0 + 0j, 1.0 + 0j
        total_remote_phase = 1.0 + 0j
        for idx, raw_str in enumerate(raw_states):
            if raw_str is None: continue
            parts = raw_str.split(",")
            c_zero *= complex(float(parts[0]), float(parts[1]))
            c_one *= complex(float(parts[2]), float(parts[3]))
            if len(parts) >= 7:
                c_phase = complex(float(parts[5]), float(parts[6]))
                if np.abs(c_phase) > 1e-15:
                    total_remote_phase *= c_phase

        with simulation_lock:
            a, b = hsq_qubit.a, hsq_qubit.b
            theta = payload.delta_phi
            p_zero = np.abs(c_zero)**2
            p_one = np.abs(c_one)**2

            if gate_name == "swap":
                # 完全繼承遠端節點狀態與相位（實體系統中，遠端也需要向本節點執行一次 SWAP 呼叫）
                hsq_qubit.a = c_zero
                hsq_qubit.b = c_one
                hsq_qubit.phase_chain_factor = total_remote_phase

            elif gate_name in ["cnot", "cnot_interlock", "bell", "multi_tensor_interlock"]:
                hsq_qubit.a = c_zero * a + c_one * b
                hsq_qubit.b = c_zero * b + c_one * a
                hsq_qubit.phase_chain_factor *= total_remote_phase

            elif gate_name in ["cphase", "controlled_phase", "cr"]:
                phase_f = np.exp(1j * theta)
                hsq_qubit.a = (c_zero + c_one) * a
                hsq_qubit.b = c_zero * b + c_one * (b * phase_f)
                hsq_qubit.phase_chain_factor *= phase_f

            elif gate_name == "ch":
                op_a = (a + b) / np.sqrt(2)
                op_b = (a - b) / np.sqrt(2)
                hsq_qubit.a = c_zero * a + c_one * op_a
                hsq_qubit.b = c_zero * b + c_one * op_b
                
            elif gate_name == "cy":
                op_a = -1j * b
                op_b = 1j * a
                hsq_qubit.a = c_zero * a + c_one * op_a
                hsq_qubit.b = c_zero * b + c_one * op_b
                hsq_qubit.phase_chain_factor *= (-1j * p_one + 1.0 * p_zero)

            elif gate_name == "cz":
                hsq_qubit.a = c_zero * a + c_one * a
                hsq_qubit.b = c_zero * b - c_one * b
                hsq_qubit.phase_chain_factor *= (-1.0 * p_one + 1.0 * p_zero)

            elif gate_name == "cs":
                hsq_qubit.a = c_zero * a + c_one * a
                hsq_qubit.b = c_zero * b + c_one * (1j * b)
                hsq_qubit.phase_chain_factor *= (1j * p_one + 1.0 * p_zero)

            elif gate_name == "ct":
                phase_t = np.exp(1j * np.pi / 4.0)
                hsq_qubit.a = c_zero * a + c_one * a
                hsq_qubit.b = c_zero * b + c_one * (phase_t * b)
                hsq_qubit.phase_chain_factor *= (phase_t * p_one + 1.0 * p_zero)

            elif gate_name == "cu":
                lam = payload.lambda_angle
                phi_ang = payload.phi_angle
                op_a = a * np.cos(theta/2) - b * np.exp(1j * lam) * np.sin(theta/2)
                op_b = a * np.exp(1j * phi_ang) * np.sin(theta/2) + b * np.exp(1j * (phi_ang + lam)) * np.cos(theta/2)
                hsq_qubit.a = c_zero * a + c_one * op_a
                hsq_qubit.b = c_zero * b + c_one * op_b

            elif gate_name == "crx":
                op_a = a * np.cos(theta/2) - 1j * b * np.sin(theta/2)
                op_b = -1j * a * np.sin(theta/2) + b * np.cos(theta/2)
                hsq_qubit.a = c_zero * a + c_one * op_a
                hsq_qubit.b = c_zero * b + c_one * op_b

            elif gate_name == "cry":
                op_a = a * np.cos(theta/2) - b * np.sin(theta/2)
                op_b = a * np.sin(theta/2) + b * np.cos(theta/2)
                hsq_qubit.a = c_zero * a + c_one * op_a
                hsq_qubit.b = c_zero * b + c_one * op_b

            elif gate_name == "crz":
                op_a = a * np.exp(-1j * theta/2)
                op_b = b * np.exp(1j * theta/2)
                hsq_qubit.a = c_zero * a + c_one * op_a
                hsq_qubit.b = c_zero * b + c_one * op_b
                hsq_qubit.phase_chain_factor *= (np.exp(1j * theta/2) * p_one + 1.0 * p_zero)

            elif gate_name == "csync_phase":
                phase_angle = np.angle(total_remote_phase)
                if abs(phase_angle) > 1e-5:
                    hsq_qubit.a = c_zero * a + c_one * b
                    hsq_qubit.b = c_zero * b - c_one * a
                    hsq_qubit.phi += np.pi * p_one  
            
            hsq_qubit.enforce_gauge_protection()

        return {"status": "success", "gate": gate_name.upper() + " INTERLOCK"}

    # 🚀 5. 單 Qubit 通用邏輯閘 (Single Qubit Local Gates)
    with simulation_lock:
        if gate_name in ["h", "hadamard"]:
            hsq_qubit.apply_hadamard_gate()
        elif gate_name in ["x", "not"]:
            hsq_qubit.apply_pauli_x_gate()
        elif gate_name == "y":
            hsq_qubit.apply_pauli_y_gate()
        elif gate_name == "z":
            hsq_qubit.apply_pauli_z_gate()
        elif gate_name == "s":
            hsq_qubit.apply_s_gate()
        elif gate_name == "t":
            hsq_qubit.apply_t_gate()
        elif gate_name == "u":
            hsq_qubit.apply_u_gate(payload.delta_phi, payload.phi_angle, payload.lambda_angle)
        elif gate_name in ["rx"]:
            hsq_qubit.apply_rx_gate(payload.delta_phi)
        elif gate_name in ["ry"]:
            hsq_qubit.apply_ry_gate(payload.delta_phi)
        elif gate_name in ["rz"]:
            hsq_qubit.apply_rz_gate(payload.delta_phi)
        elif gate_name in ["phase", "p"]:
            hsq_qubit.apply_phase_rotation_gate(payload.delta_phi)
        else:
            raise HTTPException(status_code=400, detail=f"Gate '{gate_name}' not supported")

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
        "device": "NVIDIA GPU Hardware Acceleration Direct Access Mode" if HAS_GPU else "CPU Simulation Mode",
        "version": "7.0 (The Final Puzzle - Complete Universal Tensor Set)",
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
