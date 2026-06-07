# 這是完全遵照 La Cour 2015/2016 文獻精神重構的多位元古典信號 SLWE 服務
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

class DocumentBasedSLWEEngine:
    def __init__(self, num_qubits=1):
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits  # 按照文獻，N位元對應 2^N 維古典信號分量
        
        # 初始化古典信號狀態向量於標準基態 |00...0>
        self.signal_vector = np.zeros(self.dimension, dtype=complex)
        self.signal_vector[0] = 1.0 + 0j
        
        self.current_step = 0
        self.k_delta = 0.0

    def apply_hadamard_to_all(self):
        """ 按照文獻：利用古典混頻器矩陣，對所有部署的古典信號位元施加 Hadamard 變換 """
        # 建立單位元 H 矩陣
        H_single = np.array([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2)
        
        # 透過克羅內克積 (Kronecker Product) 擴展至全域 2^N 維空間矩陣
        H_total = H_single
        for _ in range(self.num_qubits - 1):
            H_total = np.kron(H_total, H_single)
            
        # 線性信號矩陣乘法變換
        self.signal_vector = np.dot(H_total, self.signal_vector)

    def inject_phase_damping(self, noise_level=0.1):
        """ 
        文獻核心漏洞重現：古典線性信號缺乏規範剛性保護，
        隨機環境雜訊會直接侵蝕複數信號的正交相位，造成無可挽回的退相干（Decoherence）
        """
        noise = np.random.normal(0, noise_level)
        self.k_delta += noise
        
        # 模擬隨機相位對古典高階信號分量的直接侵蝕
        for i in range(1, self.dimension):
            # 越高的信號分量，受到的相位色散侵蝕越嚴重
            self.signal_vector[i] *= np.exp(1j * noise * i)

    def get_document_probability_density(self):
        """ 
        按照文獻：採集古典信號的功率譜密度 (Power Spectral Density) 
        作為模擬量子機率密度的觀測量，並映射回 500 點網格以利前端一致性繪圖
        """
        # 計算各個古典信號通道的強度平方
        intensities = np.abs(self.signal_vector) ** 2
        total_power = np.sum(intensities)
        if total_power > 0:
            intensities = intensities / total_power
            
        # 按照文獻：古典調幅信號在隨機雜訊下會退化為古典機率色散
        # 我們將 2^N 維的強度，均勻擴散映射到 500 點的網格上，模擬古典信號的色散鐘形包絡線
        x_grid = np.linspace(-20, 20, 500)
        
        # 利用信號的殘留相干強度來控制擴散寬度（相干性越低，色散越嚴重）
        coherence_leak = 1.0 - float(intensities[0]) if len(intensities) > 1 else 0.5
        width = 1.5 + coherence_leak * 4.0 + float(np.abs(self.k_delta)) * 0.1
        
        # 湧現古典色散波包
        classical_wave_profile = np.zeros(500)
        for idx, p in enumerate(intensities):
            # 每個信號分量對應不同的色散中心
            center = -3.0 + (idx * 6.0 / max(1, self.dimension - 1))
            classical_wave_profile += p * np.exp(-(x_grid - center)**2 / (2 * width**2))
            
        total_sum = np.sum(classical_wave_profile)
        if total_sum > 0:
            classical_wave_profile /= total_sum
            
        return [float(v) for v in classical_wave_profile]

# --- 啟動時由使用者互動式輸入部署的位元數量 ---
if __name__ == "__main__":
    print("====================================================")
    print("===   La Cour & Spreeuw 文獻標準：多位元 SLWE 晶片   ===")
    print("====================================================")
    
    try:
        user_qubits = int(input("請輸入要為 SLWE 部署的虛擬量子位元數量 (例如: 1, 2, 3): "))
        if user_qubits < 1: user_qubits = 1
    except ValueError:
        user_qubits = 1
        
    print(f"\n[硬體配置] 成功為本地端 SLWE 部署 {user_qubits} 個古典調幅信號位元 ({2**user_qubits} 維信號通道)")
    
    slwe_engine = DocumentBasedSLWEEngine(num_qubits=user_qubits)

    @app.route('/instruction', methods=['POST'])
    def instruction():
        data = request.get_json(silent=True) or {}
        gate_name = data.get("gate", "").lower()
        if gate_name == "h":
            slwe_engine.apply_hadamard_to_all()
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "msg": "Gate not supported"}), 400

    @app.route('/evolve', methods=['POST'])
    def evolve():
        data = request.get_json(silent=True) or {}
        noise = float(data.get('noise', 0.0))
        if noise > 0:
            slwe_engine.inject_phase_damping(noise)
        
        prob_dist = slwe_engine.get_document_probability_density()
        return jsonify({"probability_density": prob_dist})

    print("=== [Windows 本地端] SLWE 獨立微服務已就緒 ===")
    print("正在監聽 Windows 本地 Port: 5012 ...")
    app.run(host='127.0.0.1', port=5012, debug=False)
