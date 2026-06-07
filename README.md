# Container-Native Quantum Simulation Platform: Hilbert-Space Spinor Quasiparticle (HSQ) Framework

[![License: MIT](https://img.shields.io/badge/License=MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Docker Container](https://img.shields.io/badge/docker-WSL2-blue.svg)](https://www.docker.com/)

This repository implements the official source code for a container-native quantum simulation platform designed to evaluate the fault-tolerant transport dynamics of **Hilbert-Space Spinor Quasiparticles (HSQ)** under high-stress decoherence environments. 

By separating the microscopic spinor registers from macroscopic spatiotemporal wavefunctions via low-coupling microservices, this platform provides a rigorous computing benchmark comparing the novel HSQ framework against the traditional **Signal-Based Linear Wave Equation (SLWE)** approach through large-scale cluster orchestration and non-linear Quantum Random Walk (QRW) workflows.

---

## 🏗️ System Architecture & Repository Framework

The platform employs a decoupled, cloud-native microservice topology to enforce strict spatial localization and cross-node hardware isolation, eliminating numerical memory contamination inherent in global state-vector computing.

```text
+-----------------------------------------------------------------+
|            Windows Host (Main Orchestration & Control)          |
|  - Algorithm Driver & Qiskit Gate Commands: random_walk.py      |
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
📂 Manifest and File Mappingdeploy_orchestrator.py: Automated Ecosystem Purge & Orchestrator. Cleans defunct container clusters, wipes dangling registries, releases bound operating system communication ports, and dynamically scales up to $N=200$ isolated logical hardware nodes concurrently under native Linux environments.random_walk.py: Algorithmic Driver & Data Harvester. Emulates standard Qiskit-style workflows by broadcasting Hadamard coin gates, driving discrete spatiotemporal walk loops, and dynamically collecting macro evolution probability streams via heterogeneous Restful endpoints.capture_evolution_gif.py: Advanced 2D Polar Projection Visualizer. An asynchronous, non-destructive monitoring tool (compatible with Matplotlib 3.10+). It polls backend microservices and interpolates 1D spatial mesh grid density into macro 2D Polar Gauge Disk Manifolds, tracking topological phase transitions under extreme phase-damping stress./slwe_backend/slwe_local.py: Classical Linear Wave Benchmark Model. Implements the multi-qubit classical amplitude signal channel (aligned with Spreeuw 2001 & La Cour 2015/2016 models). Serves as the control group to observe the unmitigated decoherence avalanche./hsq_backend/hsq_qubit.py: Microscopic Physics Engine Service. The containerized core implementing non-linear gauge protection ($\Vert a\Vert^2 + \Vert b\Vert^2 = 1$) to combat phase dispersion./hsq_backend/Dockerfile: Hardware Manifest. Builds the lightweight Ubuntu-based container infrastructure pre-configured with the official NVIDIA CUDA 11.8.0 runtime environment to unleash real-time GPU parallel matrix computations.📊 Experimental Verification & BenchmarksThe baseline tracking evaluates a multi-step Quantum Random Walk (QRW) subjected to Phase Damping Noise. The spatial probability density distribution $P(x)$ yields distinct physical behaviors:HSQ Breakthrough (Robust Bi-modal Transport): Driven by non-linear gauge protection, the wavepacket successfully filters out phase dispersion, sustaining symmetric ballistic transport peaks at $x = \pm 10$ even under 15% noise levels.SLWE Collapse (Classical Gaussian Decay): Lacking geometric constraints, the linear continuous wave underwent an irreversible decoherence avalanche, flattening out into a classical Brownian Gaussian curve centered at $x = 0$.🚀 Quick Start & Reproducibility Guide1. Execute Cluster Orchestration and DeploymentEnsure your host environment has WSL2 (Ubuntu) activated, Docker Desktop running, and the NVIDIA Container Toolkit configured for GPU pass-through. Run the main orchestration script from your terminal to automatically reset zombie configurations and deploy a fresh 200-node logical network layout:Bashpython deploy_orchestrator.py
(Select Mode [1] or [2] and designate your target qubit scale $N$ through the interactive CLI prompt).2. Launch Algorithmic Simulation PipelineOnce the backend container matrix is active (successfully locking loopback allocation ports starting from Port 5011 onwards), open a separate shell and execute the master runtime control script to drive quantum gate injection and track step-by-step evolution:Bashpython random_walk.py
3. Generate High-Contrast 2D Topological AnalyticsTo render the publication-ready二維圓盤拓撲流形對照圖 without tampering with the isolated runtime containers, execute the non-destructive analytics script:Bashpython capture_evolution_gif.py
This tool will seamlessly assemble a high-contrast scientific asset: evolution_circular_battle.gif tracking macro topological phase shifts.
