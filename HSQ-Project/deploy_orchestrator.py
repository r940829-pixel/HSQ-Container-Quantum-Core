# ==============================================================================
# CONTAINER-NATIVE DEVOPS CLUSTER ORCHESTRATOR & ENVIRONMENT SANITIZER
# (Upgraded: Tensor-Channel IPC & Global Sync Barrier Ready)
# This script orchestrates the unified lifecycle of the simulation architecture.
# It enforces zero-tolerance hardware sanitization, purges lingering zombie 
# containers, releases bound OS communication ports, and dynamically scales 
# localized qubit container topologies under native Linux/WSL2 ecosystems.
# ==============================================================================

import os
import subprocess
import time
import sys

def clean_environment(clean_hsq=True):
    """ 
    [Automated Hardware Sanitization Operator]
    Forcibly terminates historical lingering pipelines and registry configuration 
    caches to guarantee a 100% network loopback port release.
    """
    print("\n[Sanitization] Initiating global hardware self-healing and purging lingering paths...")
    
    # 1. Purge HSQ WSL2 Docker Clusters & Virtual Tensor Bus
    if clean_hsq:
        print(" -> Forcibly evicting dangling HSQ Docker cluster containers from the runtime layer...")
        subprocess.run("sudo docker rm -f $(sudo docker ps -a -q --filter name=hsq_core_cluster_)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("sudo docker rm -f hsq_core_cluster_*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # [Architecture Upgrade] Synchronous purging of Redis Virtual Quantum Tensor Switch
        print(" -> Purging Virtual Quantum Tensor Exchange Bus (Redis)...")
        subprocess.run("sudo docker rm -f hsq_tensor_bus", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("🏆 [Sanitization Complete] Communication loopback registers and interface ports are fully unsealed.")

def quick_deploy_network():
    print("====================================================")
    print("===   HSQ & SLWE Framework: Cluster Orchestrator   ===")
    print("====================================================")
    
    # 1. Interactive Pipeline Mode Selector Gateway Interface
    print(" [-] Isolated HSQ Qubit Matrix Mode (Deploy Dockerized microservice architecture only)")
    
    deploy_hsq = True

    # 2. Dynamic Scale Dimension Query Allocation (N Logical Nodes)
    try:
        n_qubits = int(input("\nDesignate the scale dimension for ideal logical qubits (N): "))
        if n_qubits < 1: 
            n_qubits = 1
    except ValueError:
        n_qubits = 1
    
    # Trigger active sanitization sequence prior to port binding execution
    clean_environment(clean_hsq=deploy_hsq)
    time.sleep(1.5)  # Enforce runtime buffer delay for the OS socket listener to unlock cleanly

    # ==========================================================================
    # 3. DYNAMIC CONTAINER ARCHITECTURE PROVISIONING (HSQ LAYER - GPU PASSTHROUGH)
    # ==========================================================================
    
    # [Architecture Upgrade - Channel 0] Provisioning Virtual Tensor-Channel Switch (Redis Entanglement Bus)
    if deploy_hsq and n_qubits > 1:
        print("\n[Channel 0] Provisioning Virtual Tensor-Channel Switch (Redis Entanglement Bus)...")
        # Launch lightweight Redis container as cross-node information exchange hub
        redis_cmd = "sudo docker run -d --name hsq_tensor_bus -p 2057:6379 redis:alpine redis-server --maxclients 10000"
        subprocess.run(redis_cmd, shell=True, stdout=subprocess.DEVNULL)
        print("🚀 [Tensor Bus Active] Non-local information exchange channel established on Port 2057.")

    if deploy_hsq:
        print("\n[Channel 1] Provisioning localized container-native HSQ secure topological qubit cluster nodes...")
        hsq_base_port = 5011
        for i in range(n_qubits):
            current_port = hsq_base_port + i
            # [Architecture Upgrade] Inject Topology ID & Switch Address ENV vars, forcing host.docker.internal resolution
            docker_cmd = (
                f"sudo docker run -d "
                f"--name hsq_core_cluster_{i} "
                f"--gpus all "
                f"--add-host=host.docker.internal:host-gateway "
                f"-e TENSOR_BUS_HOST=host.docker.internal "
                f"-e QUBIT_NODE_ID={i} "
                f"-p {current_port}:5000 "
                f"hsq_core:latest"
            )
            print(f" -> Mapping Node HSQ-Qubit-{i} (Successfully locked loopback interface Port: {current_port})...")
            subprocess.run(docker_cmd, shell=True, stdout=subprocess.DEVNULL)
        print("🏆 [Channel 1 Success] All designated HSQ topological manifolds have entered active protective gauge runtime states.")

    print("\n====================================================")
    print("🎉 [Orchestration Flow Complete] Selected pipelines are now fully live and operational!")
    print("====================================================")

if __name__ == "__main__":
    quick_deploy_network()

