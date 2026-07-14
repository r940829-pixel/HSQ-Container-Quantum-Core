# Container-Native Quantum Simulation Platform: Hilbert-Space Spinor Quasiparticle (HSQ) Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Docker Container](https://img.shields.io/badge/docker-WSL2-lightgrey.svg)](https://www.docker.com/)
[![DOI](https://zenodo.org/badge/1259120816.svg)](https://doi.org/10.5281/zenodo.20577466)

This repository implements the official computing framework and evaluation suite for a container-native quantum simulation platform designed to benchmark the fault-tolerant transport dynamics of **Hilbert-Space Spinor Quasiparticles (HSQ)** under controlled phase-damping decoherence.

---

## 🏗️ System Architecture & Repository Framework

The platform employs a decoupled, cloud-native microservice topology to enforce strict spatial localization and cross-node hardware isolation, eliminating numerical memory contamination inherent in global state-vector computing.

---

### Set environment in linux system
install docker step1:
```bash
sudo systemctl start docker
```
install docker step2:
```bash
sudo systemctl enable docker
```
check docker version:
```bash
sudo docker --version
```
install the mod to unzip this zip file.
```bash
sudo apt update && sudo apt install unzip -y
```
pack hsq_qubit.py to make image.
```bash
sudo docker build --pull=false -t hsq_core:latest .
```

---

### connect graphics processsing unit (nvidia) with docker in linux system.
step1:
```bash
sudo apt-get update
```
step2:
```bash
sudo apt-get install -y nvidia-driver-535
```
step3:
```bash
sudo reboot
```
step4:
```bash
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```
step5:
```bash
sudo apt-get update
```
step6:
```bash
sudo apt-get install -y nvidia-container-toolkit
```
step7:
```bash
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```
step8:
```bash
sudo systemctl restart docker
```

---

### Environment Dependencies
preliminary work to install Python runtime environment.
step1:
```bash
sudo apt install python3-pip
```
step2:
```bash
sudo apt update && sudo apt install python3-venv python3-full -y
```
create your environment for python list:
```bash
python3 -m venv myenv
```
Enter your environment instruction:
```bash
source myenv/bin/activate
```
Ensure your Python runtime environment has the required auditing libraries installed:
```bash
pip install requests numpy scipy matplotlib pillow flask qiskit qiskit-aer psutil redis
```
---

### remore all container
To remore the container, enter the following command
```bash
sudo docker rm -f $(sudo docker ps -a -q)
```

---

```text
+-----------------------------------------------------------------+
|            Windows Host (Main Orchestration & Control)          |
|  - Algorithmic Driver & Data Harvester: random_walk.py          |
|  - Hardware Scaling & Throughput Profiler: benchmark_scaling.py |
|  - Dynamic DevOps Pure-Purge Orchestrator: deploy_orchestrator.py
+-----------------------------------------------------------------+
                                |
             [ Loopback Restful HTTP API Gateways ]
     (Port 5011 to N: Spawning Scalable Active Qubit Nodes)
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
```

---

```text
📂 Manifest Mapping & Component Index
deploy_orchestrator.py: Automated Ecosystem Purge & Cluster Orchestrator. Cleans defunct container clusters, wipes dangling registries, releases bound host OS communication ports, and dynamically scales up to N=100 isolated logical hardware nodes concurrently under native Linux/WSL2 environments.
random_walk.py: Top-level Execution Controller & Driver. Orchestrates the unified runtime lifecycle across >= 20 independent random seeds. It broadcasts Hadamard coin gates, drives discrete spatiotemporal walk loops, and dynamically collects macro evolution probability streams via Restful endpoints.
/hsq_backend/hsq_qubit.py: Microscopic Simulation Core. The containerized backend application core implementing non-linear mathematical normalization constraints to eliminate numerical dispersion over 500-point spatiotemporal grids.
/hsq_backend/Dockerfile: Container Infrastructure Manifest. Builds the lightweight Ubuntu-based container environment pre-configured with the official NVIDIA CUDA 11.8.0 runtime to unleash GPU parallel matrix computations.
```

---

🚀 Quick Start & Reproducibility Guide
PrerequisitesWindows 10 / 11 with WSL2 (Ubuntu Linux Kernel) enabled.
Docker Desktop active and integrated with the WSL2 backend.
NVIDIA Container Toolkit configured to allow GPU pass-through to Docker instances.
1. Execute Cluster Orchestration and Deployment
Run the main orchestration script from a Windows PowerShell or CMD terminal to automatically reset historic zombie dependencies and deploy a fresh logical network cluster(please running in wsl, if your computer system is window10/11):
```bash
python deploy_orchestrator.py
```
(Designate your target qubit scale N through the interactive CLI prompt).
2. Launch Algorithmic Simulation Pipeline
Once the backend container matrix is live and ports starting from Port 5011 are bound, open a separate shell and execute the master runtime control script to drive quantum gate injection, perform the 20-seed stress test, and compile the quantitative data:
```bash
python random_walk.py --seeds 20 --steps 20 --noise 0.00

```

---
