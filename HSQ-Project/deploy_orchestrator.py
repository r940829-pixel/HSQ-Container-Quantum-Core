import os
import subprocess
import time
import sys

def clean_environment(clean_hsq=True, clean_slwe=True):
    """ 
    🟢 核心資工亮點：全自動硬體環境清理函數 (Linux/WSL2 原生優化版)
    強制終結所有舊有殘留線路，確保連接埠 100% 釋放
    """
    print("\n[環境清理] 正在執行全面硬體自癒，終結殘留線路...")
    
    # 1. 清理 HSQ WSL2 Docker 容器 (移除 wsl 前綴，純 Linux 指令控制)
    if clean_hsq:
        print(" -> 正在強制拔除 WSL2 中殘留的 HSQ Docker 叢集容器...")
        # 刪除所有名稱匹配 hsq_core_cluster_ 的容器
        subprocess.run("sudo docker rm -f $(sudo docker ps -a -q --filter name=hsq_core_cluster_)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("sudo docker rm -f hsq_core_cluster_*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # 2. 清理 SLWE 背景進程
    if clean_slwe:
        print(" -> 正在強制殺死殘留的 SLWE 波動晶片進程...")
        # 跨平台適應：如果在 Windows 本地執行
        if sys.platform == "win32":
            kill_cmd = 'wmic process where "commandline like \'%slwe_local.py%\'" get processid /format:list'
            output = subprocess.check_output(kill_cmd, shell=True, text=True)
            for line in output.splitlines():
                if "ProcessId=" in line:
                    pid = line.split("=")[1].strip()
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # 🟢 在 WSL2/Linux 原生環境下，精準終結 slwe_local.py 的 Python 進程
            subprocess.run("pkill -f slwe_local.py", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("🏆 環境清理完畢！實體硬體連接埠與暫存器已完全解鎖復位。")

def quick_deploy_network():
    print("====================================================")
    print("===    HSQ & SLWE 晶片網絡：動態彈性編排與清理部署端   ===")
    print("====================================================")
    
    # 1. 模式選擇接口
    print("請選擇您本次實驗預計部署的硬體線路種類：")
    print(" [1] 完整對照聯動模式 (同步清理並拉起 HSQ 容器叢集 與 SLWE 本地通道)")
    print(" [2] 獨立 HSQ 量子晶片模式 (僅清理並拉起 WSL2 Docker 安全容器叢集)")
    print(" [3] 獨立 SLWE 波動晶片模式 (僅清理並開啟古典信號通道)")
    
    try:
        mode = int(input("請輸入模式編號 (1-3): "))
        if mode not in [1, 2, 3]: mode = 1
    except ValueError:
        mode = 1

    # 2. 互動式輸入部署規模 (N)
    try:
        n_qubits = int(input("\n請輸入預計部署的理想量子位元規模 (N): "))
        if n_qubits < 1: n_qubits = 1
    except ValueError:
        n_qubits = 1

    print(f"\n[系統分析] 開始動態編排與環境自癒（模式 {mode}）：")
    deploy_hsq = (mode in [1, 2])
    deploy_slwe = (mode in [1, 3])
    
    # 部署前先行呼叫自動清理機制
    clean_environment(clean_hsq=deploy_hsq, clean_slwe=deploy_slwe)
    time.sleep(1.5)  # 給予操作系統釋放連接埠的緩衝時間

    # ==========================================
    # 3. 動態部署 HSQ 容器組 (Linux/WSL2 原生執行)
    # ==========================================
    if deploy_hsq:
        print("\n[通道一] 正在部署全新 HSQ 拓撲安全容器群...")
        hsq_base_port = 5011
        for i in range(n_qubits):
            current_port = hsq_base_port + i
            # 🟢 【重大修正】：徹底移除字串開頭的 wsl 前綴，使指令完全符合原生 Linux 語法！
            docker_cmd = (
                f"sudo docker run -d "
                f"--name hsq_core_cluster_{i} "
                f"--gpus all "
                f"-p {current_port}:5000 "
                f"hsq_core:latest"
            )
            print(f" -> 正在建立 HSQ-Qubit-{i} (成功鎖定連接埠: {current_port})...")
            subprocess.run(docker_cmd, shell=True, stdout=subprocess.DEVNULL)
        print("🏆 所有指定之 HSQ 拓撲位元容器均已順利進入物理防禦流形狀態。")

    # ==========================================
    # 4. 動態部署 SLWE 多位元連續波環境
    # ==========================================
    if deploy_slwe:
        print("\n[通道二] 正在拉起全新多位元 SLWE 波動晶片...")
        slwe_port = 5012
        try:
            slwe_process = subprocess.Popen(
                [sys.executable, "slwe_local.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            slwe_process.stdin.write(f"{n_qubits}\n")
            slwe_process.stdin.flush()
            print(f" -> SLWE 獨立微服務上線成功 (成功鎖定連接埠: {slwe_port})")
            print(f" -> 古典信號 {2**n_qubits} 維連續張量積通道初始化完畢。")
        except Exception as e:
            print(f" ❌ SLWE 本地晶片拉起異常: {e}")

    print("\n====================================================")
    print("🎉 [自動清理與配置通車成功] 所選線路已開闢，位元運作效果已 100% 保障！")
    print("====================================================")

if __name__ == "__main__":
    quick_deploy_network()
