# Container-Native Quantum Simulation Platform: Hilbert-Space Spinor Quasiparticle (HSQ) Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Docker Container](https://img.shields.io/badge/docker-WSL2-blue.svg)](https://www.docker.com/)

This repository implements the official computing framework and evaluation suite for a container-native quantum simulation platform designed to benchmark the fault-tolerant transport dynamics of **Hilbert-Space Spinor Quasiparticles (HSQ)** under high-stress phase-damping decoherence.

By isolating microscopic spinor registers inside lightweight **Docker microservices** under **WSL2** and leveraging **NVIDIA CUDA** parallelization, this platform provides a rigorous verification environment to contrast the non-linear HSQ framework against the traditional **Signal-Based Linear Wave Equation (SLWE)** benchmark through discrete Quantum Random Walk (QRW) workflows.

---

## 🏗️ System Architecture & Repository Framework

The platform employs a decoupled, cloud-native microservice topology to enforce strict spatial localization and cross-node hardware isolation, eliminating numerical memory contamination inherent in global state-vector computing.

```text
+-----------------------------------------------------------------+
|            Windows Host (Main Orchestration & Control)          |
|  - Algorithmic Driver & Qiskit Gate Injection: random_walk.py   |
|  - Dynamic DevOps Pure-Purge Orchestrator: deploy_orchestrator.py
+-----------------------------------------------------------------+
                                |
             [ Loopback Restful HTTP API Gateways ]
             (Port 5011 to 5210: Spawning Scalable Active Qubit Nodes)
                                |
                                v
+-----------------------------------------------------------------+
|           WSL2 Linux Kernel / Docker Microservice Cluster        |
|  - Hardware Isolation Environment (Defined via /hsq_backend/Dockerfile)
|  - Real-time Solver & Gauge Protection Service: hsq_qubit.py    |
+-----------------------------------------------------------------+
                                |
             [ NVIDIA Container Toolkit Pass-through ]
                                v
+-----------------------------------------------------------------+
|               NVIDIA GPU CUDA Acceleration Layer                |
|  - CuPy-driven Parallelized Continuous Wavepacket Evolution     |
|  - Active Mass Integration via Spinor-Momentum Locking          |
+-----------------------------------------------------------------+
📂 Repository Manifesto & Manifest Mapping
deploy_orchestrator.py: Automated Ecosystem Purge & Cluster Orchestrator. Cleans defunct container clusters, wipes dangling registries, releases bound host OS communication ports, and dynamically scales up to N=200 isolated logical hardware nodes concurrently under native Linux/WSL2 environments.
random_walk.py: Top-level Execution Controller & Driver. Orchestrates the unified runtime lifecycle. It emulates standard Qiskit-style workflows by broadcasting Hadamard coin gates, driving discrete spatiotemporal walk loops, and dynamically collecting macro evolution probability streams via heterogeneous Restful endpoints.
capture_evolution_gif.py: Advanced 2D Polar Projection Visualizer. An asynchronous, non-destructive monitoring tool (compatible with Matplotlib 3.10+ and Python 3.13). It polls backend microservices and interpolates 1D spatial mesh grid arrays into macro 2D Polar Gauge Disk Manifolds, tracking topological phase transitions under severe environmental noise (Noise = 1.00).
/slwe_backend/slwe_local.py: Classical Linear Wave Benchmark Model. Implements the multi-qubit classical amplitude signal channel (aligned with Spreeuw 2001 & La Cour 2015/2016 models) running on a local Flask endpoint. Serves as the experimental control group to observe the unmitigated decoherence avalanche.
/hsq_backend/hsq_qubit.py: Microscopic Physics Engine Service. The containerized backend application core implementing non-linear gauge metric protection to combat numerical phase dispersion over 500-point spatiotemporal grids.
/hsq_backend/Dockerfile: Hardware Environment Manifest. Builds the lightweight Ubuntu-based container infrastructure pre-configured with the official NVIDIA CUDA 11.8.0 runtime environment to unleash real-time GPU parallel matrix computations (optimized with CuPy, NumPy, and Flask dependencies).
📊 Experimental Verification & Benchmarks
The baseline tracking evaluates a multi-step Quantum Random Walk (QRW) subjected to Phase Damping Noise. The spatial probability density distribution P(x) yields distinct physical behaviors:
HSQ Breakthrough (Robust Bi-modal Transport): Driven by non-linear gauge protection, the wavepacket successfully filters out phase dispersion, sustaining symmetric ballistic transport peaks at x = +- 10 even under 15% noise levels.
SLWE Collapse (Classical Gaussian Decay): Lacking geometric constraints, the linear continuous wave underwent an irreversible decoherence avalanche, flattening out into a classical Brownian Gaussian curve centered at x = 0.
🚀 Quick Start & Reproducibility Guide
1. Execute Cluster Orchestration and Deployment
Ensure your host environment has WSL2 (Ubuntu) activated, Docker Desktop running, and the NVIDIA Container Toolkit configured for GPU pass-through. Run the main orchestration script from your terminal to automatically reset zombie configurations and deploy a fresh 200-node logical network layout:
python deploy_orchestrator.py
(Select Mode [1] or [2] and designate your target qubit scale N through the interactive CLI prompt).
2. Launch Algorithmic Simulation Pipeline
Once the backend container matrix is active (successfully locking loopback allocation ports starting from Port 5011 onwards), open a separate shell and execute the master runtime control script to drive quantum gate injection and track step-by-step evolution:
python random_walk.py
Generate High-Contrast 2D Topological Analytics
To render the publication-ready 二維圓盤拓撲流形對照圖 without tampering with the isolated runtime containers, execute the non-destructive analytics script:
python capture_evolution_gif.py
This tool will seamlessly assemble a high-contrast scientific asset: evolution_circular_battle.gif tracking macro topological phase shifts from t=0.1 to t=10.0 fs.
🎓 Peer-Review and IEEE Journal Security Token
For IEEE double-blind peer-review purposes, this repository is hosted on Anonymous GitHub to fully protect author identity before formal acceptance. Reviewers can seamlessly access and inspect the full unredacted source code framework online.
🔗 Digital Object Identifier (DOI) and Citation
Note: The permanent Digital Object Identifier (DOI) via Zenodo registry will be unsealed and appended below post-defense upon transitioning this archive into a Public Open-Source Repository.
To cite this hardware architecture framework in your research:
Zhuang, H. (2026). A Novel Spinor Quasiparticle Architecture over Hilbert Space Decoupling Framework. GitHub Repository. DOI: [Pending Post-Acceptance Activation]
