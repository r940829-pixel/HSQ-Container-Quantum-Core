# Container-Native Quantum Simulation Platform: Hilbert-Space Spinor Quasiparticle (HSQ) Framework

This repository implements an open-source, container-native quantum simulation platform designed to evaluate the fault-tolerant transport dynamics of **Hilbert-Space Spinor Quasiparticles (HSQ)** under severe decoherence environments. 

By leveraging **Docker microservices** for spatial localization and **NVIDIA CUDA (via CuPy)** for hardware-accelerated grid evolution, this platform provides a rigorous benchmark comparing the novel HSQ framework against the traditional **Signal-Based Linear Wave Equation (SLWE)** approach through non-linear Quantum Random Walk (QRW) simulations.

---

## 🏗️ System Architecture

The platform utilizes a decoupled, cloud-native microservice architecture to enforce strict spatial localization and isolation of quantum nodes, eliminating memory contamination issues inherent in global state-vector simulators.

+-----------------------------------------------------------------+
|               Windows Host (Main Orchestration Layer)           |
|   - Algorithm Scheduling & Quantum Coin Gate Assignment         |
|   - Phase Damping Noise Injection Control                       |
|   - Execution Script: hsq_random_walk.py                        |
+-----------------------------------------------------------------+
|
[ Loopback Restful HTTP API 通道 ]
(Port 5000: HSQ Qubit | Port 5001: SLWE Qubit)
|
v
+-----------------------------------------------------------------+
|               WSL2 / Docker Microservice Cluster                |
|   - Hardware Isolation (Container-per-Qubit)                    |
|   - Non-linear Gauge Metric Protection: ||a||² + ||b||² = 1     |
+-----------------------------------------------------------------+
|
[ NVIDIA Container Toolkit Pass-through ]
|
v
+-----------------------------------------------------------------+
|                  NVIDIA GeForce GPU Acceleration                |
|   - CUDA Parallel Computing Layer                               |
|   - Solving Continuous Spatiotemporal Wavepacket Evolution ξ(x,t)|
+-----------------------------------------------------------------+


---

## 🔬 Core Experiment: Quantum Random Walk (QRW) under Decoherence

The core benchmark of this repository focuses on a **10-Step Quantum Random Walk** subjected to **15.0% Phase Damping Noise**. 

### 1. Hilbert-Space Spinor Quasiparticle (HSQ) Framework
The HSQ framework incorporates a non-linear gauge protection filter ($\|a\|^2 + \|b\|^2 = 1$). Upon noise injection, the state vector is instantly projected back onto the Bloch spherical metric, manifesting a self-focusing effect that filters out phase dispersion.

### 2. Signal-Based Linear Wave Equation (SLWE) Approach
The traditional SLWE approach treats the qubit as a pure linear wave superposition without geometric constraints. Consequently, phase damping noise destroys the off-diagonal coherence elements irreversibly.

---

## 📊 Experimental Results & Emergence Visualizer

When executing `hsq_random_walk.py`, the platform aggregates runtime spatiotemporal wavepacket profile data from the backend containers and generates the following spatial probability density distribution $P(x)$:

       Quantum Random Walk Spatial Profile (Noise: 15.0%)
0.040 +---------------------------------------------------------+
|                                                         |
0.035 |          /\                                   /\        |
|         /  \                                 /  \       |
0.030 |        /    \       - - - - - - -           /    \      |
|       /      \     /             \         /      \     |
0.025 |      /        \   /               \       /        \    |
|     /          _/                 _    /          \   |
0.020 |    /                                 \  /            \  |
|   /                                   /              \ |
0.015 |  /                                                     |
| /

0.010 |/

+---------------------------------------------------------+
-20        -10          0           10          20
Spatial Grid Position (x)

    _______  HSQ New Method (Robust Bi-modal Distribution)
    - - - -  SLWE Traditional Method (Degenerated Classical Gaussian)

### Key Scientific Findings:
* **HSQ Breakthrough (Green Solid Line)**: Despite the 15% phase damping noise, the HSQ framework successfully preserves the sharp, symmetric **Bi-modal Distribution** at $x = \pm 10$. This demonstrates ballistic transport driven by persistent quantum coherence and strict gauge protection.
* **SLWE Collapse (Red Dashed Line)**: Lacking geometric constraints, the traditional SLWE framework undergoes complete quantum decoherence. The spatial profile collapses into a standard **Classical Gaussian Bell Curve** centered at $x = 0$, degenerating the system behavior into classical Brownian motion.

---

## 🚀 Quick Start & Deployment Guide

### Prerequisites
* Windows 10/11 with WSL2 enabled.
* Docker Desktop with WSL2 backend integration.
* NVIDIA GPU with CUDA Driver installed on the host.
* NVIDIA Container Toolkit installed inside the WSL2/Docker environment.

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/HSQ-Container-Quantum-Core.git](https://github.com/your-username/HSQ-Container-Quantum-Core.git)
cd HSQ-Container-Quantum-Core
2. Build and Deploy Backend Qubit Containers (Ubuntu/WSL2 Terminal)
Deploy the robust HSQ node and the traditional SLWE comparison node onto your GPU hardware simultaneously:

Bash
# Build the images using respective Dockerfiles
docker build -t hsq-qubit-core:v1 ./hsq_backend
docker build -f Dockerfile_SLWE -t slwe-qubit-core:v1 ./slwe_backend

# Run containers in background with GPU access and port mappings
docker run -d --name hsq_q0 --gpus all -p 5000:5000 hsq-qubit-core:v1
docker run -d --name traditional_slwe_q0 --gpus all -p 5001:5001 slwe-qubit-core:v1
3. Verify Container Health Status
Bash
curl [http://127.0.0.1:5000/ping](http://127.0.0.1:5000/ping)
curl [http://127.0.0.1:5001/ping](http://127.0.0.1:5001/ping)
4. Execute Frontend Spatiotemporal Simulation (Windows CMD / IDE)
Run the orchestration script to initiate the 15% noise stress-test and view the real-time Matplotlib spatial interference plot:

DOS
python hsq_random_walk.py
🎓 Citation & Academic Contribution
This repository serves as the official implementation for verifying gauge-protected quasiparticle transport dynamics in localized computational spaces. The architectural decoupled microservice framework verified herein demonstrates a scalable path toward distributed virtual quantum cloud clusters.