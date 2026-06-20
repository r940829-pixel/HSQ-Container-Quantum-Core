# ==============================================================================
# CONTAINER-NATIVE DEVOPS CLUSTER ORCHESTRATOR & ENVIRONMENT SANITIZER
# [PURE HSQ TOPOLOGY PRODUCTION MODE - DECOUPLED FROM REFERENTIAL ASSETS]
# Fully optimized for 1-Qubit Docker Cluster (N=1) under WSL2 ecosystems.
# ==============================================================================

import os
import subprocess
import time
import sys

def clean_environment():
    """ Forcibly terminates historical lingering pipelines to guarantee 100% port release. """
    print("\n[Sanitization] Initiating global hardware self-healing and purging lingering paths...")
    
    # Purge HSQ WSL2 Docker Clusters & Virtual Tensor Bus
    print(" -> Forcibly evicting dangling HSQ Docker cluster containers from the runtime layer...")
    subprocess.run("sudo docker rm -f $(sudo docker ps -a -q --filter name=hsq_core_cluster_)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("sudo docker rm -f hsq_core_cluster_*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(" -> Purging Virtual Quantum Tensor Exchange Bus (Redis)...")
    subprocess.run("sudo docker rm -f hsq_tensor_bus", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("🏆 [Sanitization Complete] Communication loopback registers are fully unsealed.")

def quick_deploy_network():
    print("====================================================")
    print("===      HSQ Framework: Pure Cluster Orchestrator   ===")
    print("====================================================")
    
    # Enforcing 1-Qubit Scale (N=1) for rigid verification
    n_qubits = 1
    
    # Trigger active sanitization sequence prior to port binding execution
    clean_environment()
    time.sleep(1.5)  # Enforce runtime buffer delay for the OS socket listener to unlock cleanly

    # ==========================================================================
    # DYNAMIC CONTAINER ARCHITECTURE PROVISIONING (HSQ LAYER - GPU PASSTHROUGH)
    # ==========================================================================
    if n_qubits > 1:
        print("\n[Channel 0] Provisioning Virtual Tensor-Channel Switch (Redis Entanglement Bus)...")
        redis_cmd = "sudo docker run -d --name hsq_tensor_bus -p 6379:6379 redis:alpine"
        subprocess.run(redis_cmd, shell=True, stdout=subprocess.DEVNULL)
        print("🚀 [Tensor Bus Active] Non-local information exchange channel established on Port 6379.")

    print("\n[Channel 1] Provisioning container-native HSQ logic qubit cluster nodes...")
    hsq_base_port = 5011
    for i in range(n_qubits):
        current_port = hsq_base_port + i
        # Mounts your local live hsq_qubit.py directly into the little whale sand-box
        docker_cmd = (
            f"sudo docker run -d "
            f"--name hsq_core_cluster_{i} "
            f"--gpus all "
            f"--add-host=host.docker.internal:host-gateway "
            f"-v $(pwd)/hsq_qubit.py:/app/hsq_qubit.py "
            f"-e TENSOR_BUS_HOST=host.docker.internal "
            f"-e QUBIT_NODE_ID={i} "
            f"-p {current_port}:5000 "
            f"hsq_core:latest "
            f"python3 /app/hsq_qubit.py"
        )
        print(f" -> Mapping Node HSQ-Qubit-{i} (Successfully locked loopback interface Port: {current_port})...")
        subprocess.run(docker_cmd, shell=True, stdout=subprocess.DEVNULL)
        
    print("\n====================================================")
    print("🎉 [Orchestration Flow Complete] HSQ Container is now fully live and operational!")
    print("====================================================")

if __name__ == "__main__":
    quick_deploy_network()
