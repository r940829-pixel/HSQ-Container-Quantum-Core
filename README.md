# Container-Native Quantum Simulation Platform: Hilbert-Space Spinor Quasiparticle (HSQ) Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Docker Container](https://img.shields.io/badge/docker-WSL2-lightgrey.svg)](https://www.docker.com/)

This repository implements the official computing framework and evaluation suite for a container-native quantum simulation platform designed to benchmark the fault-tolerant transport dynamics of **Hilbert-Space Spinor Quasiparticles (HSQ)** under controlled phase-damping decoherence.

By isolating microscopic spinor registers inside lightweight **Docker microservices** under **WSL2** and leveraging **NVIDIA CUDA** parallelization via CuPy, this platform provides a rigorous verification environment to contrast the non-linear HSQ framework against the traditional **Signal-Based Linear Wave Equation (SLWE)** reference baseline through multi-seed discrete Quantum Random Walk (QRW) workflows.

---

## 🏗️ System Architecture & Repository Framework

The platform employs a decoupled, cloud-native microservice topology to enforce strict spatial localization and cross-node hardware isolation, eliminating numerical memory contamination inherent in global state-vector computing.

```text
+-----------------------------------------------------------------+
|            Windows Host (Main Orchestration & Control)          |
|  - Algorithmic Driver & Data Harvester: random_walk.py          |
|  - Hardware Scaling & Throughput Profiler: benchmark_scaling.py |
|  - Dynamic DevOps Pure-Purge Orchestrator: deploy_orchestrator.py
+-----------------------------------------------------------------+
                                |
             [ Loopback Restful HTTP API Gateways ]
     (Port 5011 to 5110: Spawning Scalable Active Qubit Nodes)
     (Port 6000: Isolated Reference Baseline Channel Allocation)
                                |
                                v
+-----------------------------------------------------------------+
|           WSL2 Linux Kernel / Docker Microservice Cluster        |
|  - Environment Isolation defined via /hsq_backend/Dockerfile    |
|  - Real-time Solver & Unitary Verification: hsq_qubit.py        |
+-----------------------------------------------------------------+
                                |
             [ NVIDIA Container Toolkit Pass-through ]
                                v
+-----------------------------------------------------------------+
|               NVIDIA GPU CUDA Acceleration Layer                |
|  - CuPy-driven Parallelized Continuous Wavepacket Evolution     |
|  - Unitary Conserved Manifold via Spinor-Momentum Constraint    |
+-----------------------------------------------------------------+
📂 Manifest Mapping & Component Index
deploy_orchestrator.py: Automated Ecosystem Purge & Cluster Orchestrator. Cleans defunct container clusters, wipes dangling registries, releases bound host OS communication ports, and dynamically scales up to N=100 isolated logical hardware nodes concurrently under native Linux/WSL2 environments.
random_walk.py: Top-level Execution Controller & Driver. Orchestrates the unified runtime lifecycle across >= 20 independent random seeds. It broadcasts Hadamard coin gates, drives discrete spatiotemporal walk loops, and dynamically collects macro evolution probability streams via Restful endpoints.
benchmark_scaling.py: Computational Scaling Profiler. Measures execution latency per step across scaling layers (N=10 to N=100) and tracks real-time host hardware speedups (CPU NumPy vs. GPU CuPy).
capture_evolution_gif.py: 2D Polar Projection Visualizer. An asynchronous, non-destructive monitoring tool compatible with Matplotlib 3.10+ and Python 3.13. It polls backend microservices and interpolates 1D spatial mesh grid arrays into macro 2D Polar Gauge Disk Manifolds.
/slwe_backend/slwe_local.py: Classical Linear Wave Reference Model. Implements the multi-qubit classical amplitude signal channel (aligned with Spreeuw 2001 & La Cour 2015/2016 models) running on Port 6000. Serves as the experimental control group to observe the unmitigated phase dispersion.
/hsq_backend/hsq_qubit.py: Microscopic Simulation Core. The containerized backend application core implementing non-linear mathematical normalization constraints to eliminate numerical dispersion over 500-point spatiotemporal grids.
/hsq_backend/Dockerfile: Container Infrastructure Manifest. Builds the lightweight Ubuntu-based container environment pre-configured with the official NVIDIA CUDA 11.8.0 runtime to unleash GPU parallel matrix computations.
📊 Quantitative Benchmarks & Experimental Verification
The verification suite evaluates a 10-step Quantum Random Walk (QRW) subjected to a 10.0% Phase Damping Noise floor across 20 independent seeds. The harvested metrics yield distinct statistical and physical behaviors:
Computational Accuracy vs. Analytical(Table I):
Quantum Fidelity (F): 97.557% (Demonstrating tight convergence with Qiskit Aer baseline profiles).
Total Variation Distance (TVD): 0.116835 (Strictly bounded under formal information-theoretic inequality limits).
Multi-Seed Environmental Robustness Analysis (Table II):
HSQ Wavepacket Integrity: 0.9635 +- 0.0037 (Sustaining sharp symmetric transport peaks ).
SLWE Wavepacket Integrity: 0.2439 +- 0.0091 (Undergoing an irreversible decoherence avalanche and collapsing into a classical Brownian distribution with a Peak-to-Valley ratio approaching 1.0).
Host Computer Hardware Scaling Performance (Table III):
GPU Accelerated Runtime: Constant at 0.45ms per step across all scaling limits, bypassing OS kernel thread scheduling overhead.
Maximum Acceleration Ratio: Spontaneous emergence at the extreme (N=100 concurrent microservice nodes).
🚀 Quick Start & Reproducibility Guide
PrerequisitesWindows 10 / 11 with WSL2 (Ubuntu Linux Kernel) enabled.
Docker Desktop active and integrated with the WSL2 backend.
NVIDIA Container Toolkit configured to allow GPU pass-through to Docker instances.
1. Execute Cluster Orchestration and Deployment
Run the main orchestration script from a Windows PowerShell or CMD terminal to automatically reset historic zombie dependencies and deploy a fresh logical network cluster:
python deploy_orchestrator.py
(Designate your target qubit scale N through the interactive CLI prompt).
2. Launch Algorithmic Simulation Pipeline
Once the backend container matrix is live and ports starting from Port 5011 are bound, open a separate shell and execute the master runtime control script to drive quantum gate injection, perform the 20-seed stress test, and compile the quantitative data:
python random_walk.py
This script will output the formal grayscale table_2_noise_stress.png and the 300 DPI publication-grade English spatial wavepacket chart fig2_qrw_ablation_profile.png.
3.Generate Hardware Scaling Analytics
To perform live CPU/GPU parallel computing benchmarks and evaluate time complexity scaling curves, execute the benchmarking tool:
python benchmark_scaling.py
This will compile the host machine's runtime specs and save the dual-axes manuscript chart fig7_hardware_scaling_curve.png complete with mathematical error bars.
🎓 Peer-Review and IEEE Journal Access TokenFor double-blind peer-review purposes, this repository is hosted on Anonymous GitHub to protect author identity prior to formal acceptance. Reviewers can access, inspect, and independently reproduce the full unredacted source code framework.
🔗 Digital Object Identifier (DOI) and CitationNote: The permanent Digital Object Identifier (DOI) archive token issued via the Zenodo registry will be unsealed and appended below upon transitioning this archive into a Public Open-Source Repository post-defense.
To cite this hardware architecture framework in your research:
Zhuang, H. (2026). A Container-Native Quantum Simulation Platform over Hilbert Space 
