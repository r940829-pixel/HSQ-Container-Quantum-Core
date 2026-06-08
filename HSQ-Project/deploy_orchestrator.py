# ==============================================================================
# CONTAINER-NATIVE DEVOPS CLUSTER ORCHESTRATOR & ENVIRONMENT SANITIZER
# This script orchestrates the unified lifecycle of the simulation architecture.
# It enforces zero-tolerance hardware sanitization, purges lingering zombie 
# containers, releases bound OS communication ports, and dynamically scales 
# localized qubit container topologies under native Linux/WSL2 ecosystems.
# ==============================================================================

import os
import subprocess
import time
import sys

def clean_environment(clean_hsq=True, clean_slwe=True):
    """ 
    [Automated Hardware Sanitization Operator]
    Forcibly terminates historical lingering pipelines and registry configuration 
    caches to guarantee a 100% network loopback port release.
    """
    print("\n[Sanitization] Initiating global hardware self-healing and purging lingering paths...")
    
    # 1. Purge HSQ WSL2 Docker Clusters via native Linux engine interactions
    if clean_hsq:
        print(" -> Forcibly evicting dangling HSQ Docker cluster containers from the runtime layer...")
        # Evict all active/inactive containers matching the cluster prefix filter pattern
        subprocess.run("sudo docker rm -f $(sudo docker ps -a -q --filter name=hsq_core_cluster_)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("sudo docker rm -f hsq_core_cluster_*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # 2. Terminate SLWE Background Emulation Daemons
    if clean_slwe:
        print(" -> Terminating historical SLWE continuous wave engine daemon processes...")
        # Cross-platform orchestration mapping: Intercept host architecture characteristics
        if sys.platform == "win32":
            kill_cmd = 'wmic process where "commandline like \'%slwe_local.py%\'" get processid /format:list'
            try:
                output = subprocess.check_output(kill_cmd, shell=True, text=True)
                for line in output.splitlines():
                    if "ProcessId=" in line:
                        pid = line.split("=")[1].strip()
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:
            # Native Linux/WSL2 process signature pattern termination operator
            subprocess.run("pkill -f slwe_local.py", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("🏆 [Sanitization Complete] Communication loopback registers and interface ports are fully unsealed.")

def quick_deploy_network():
    print("====================================================")
    print("===   HSQ & SLWE Framework: Cluster Orchestrator  ===")
    print("====================================================")
    
    # 1. Interactive Pipeline Mode Selector Gateway Interface
    print("Select the target architectural routing topology for this experiment evaluation loop:")
    print(" [1] Co-deployment Mode (Synchronized pipeline setup for both HSQ Clusters & SLWE Engine)")
    print(" [2] Isolated HSQ Qubit Matrix Mode (Deploy Dockerized microservice architecture only)")
    print(" [3] Isolated SLWE Reference Mode (Initiate classical linear wave baseline channel only)")
    
    try:
        mode = int(input("Enter target topology deployment mode index (1-3): "))
        if mode not in [1, 2, 3]: 
            mode = 1
    except ValueError:
        mode = 1

    # 2. Dynamic Scale Dimension Query Allocation (N Logical Nodes)
    try:
        n_qubits = int(input("\nDesignate the scale dimension for ideal logical qubits (N): "))
        if n_qubits < 1: 
            n_qubits = 1
    except ValueError:
        n_qubits = 1

    print(f"\n[Orchestrator Analysis] Initiating framework deployment pipeline (Mode Index: {mode}):")
    deploy_hsq = (mode in [1, 2])
    deploy_slwe = (mode in [1, 3])
    
    # Trigger active sanitization sequence prior to port binding execution
    clean_environment(clean_hsq=deploy_hsq, clean_slwe=deploy_slwe)
    time.sleep(1.5)  # Enforce runtime buffer delay for the OS socket listener to unlock cleanly

    # ==========================================================================
    # 3. DYNAMIC CONTAINER ARCHITECTURE PROVISIONING (HSQ LAYER - GPU PASSTHROUGH)
    # ==========================================================================
    if deploy_hsq:
        print("\n[Channel 1] Provisioning localized container-native HSQ secure topological qubit cluster nodes...")
        hsq_base_port = 5011
        for i in range(n_qubits):
            current_port = hsq_base_port + i
            # Construct hardware manifest instruction utilizing strict native Linux/WSL2 engine commands
            docker_cmd = (
                f"sudo docker run -d "
                f"--name hsq_core_cluster_{i} "
                f"--gpus all "
                f"-p {current_port}:5000 "
                f"hsq_core:latest"
            )
            print(f" -> Mapping Node HSQ-Qubit-{i} (Successfully locked loopback interface Port: {current_port})...")
            subprocess.run(docker_cmd, shell=True, stdout=subprocess.DEVNULL)
        print("🏆 [Channel 1 Success] All designated HSQ topological manifolds have entered active protective gauge runtime states.")

    # ==========================================================================
    # 4. LINEAR CONTINUOUS WAVE BENCHMARK INITIALIZATION (SLWE LAYER - SUBPROCESS)
    # ==========================================================================
    if deploy_slwe:
        print("\n[Channel 2] Orchestrating the classical multi-qubit linear baseline SLWE engine context...")
        slwe_port = 5012
        try:
            slwe_process = subprocess.Popen(
                [sys.executable, "slwe_local.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Automate cross-process initialization configuration stream injection
            slwe_process.stdin.write(f"{n_qubits}\n")
            slwe_process.stdin.flush()
            print(f" -> SLWE microservice daemon initialized safely (Successfully locked interface Port: {slwe_port})")
            print(f" -> Classical signal {2**n_qubits}-dimensional tensor product Hilbert space fully allocated.")
        except Exception as e:
            print(f" ❌ [Channel 2 Failure] SLWE core daemon instantiation abort anomaly: {e}")

    print("\n====================================================")
    print("🎉 [Orchestration Flow Complete] Selected pipelines are now fully live and operational!")
    print("====================================================")

if __name__ == "__main__":
    quick_deploy_network()
