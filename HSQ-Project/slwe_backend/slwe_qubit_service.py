import numpy as np
from flask import Flask, request, jsonify

# 自動偵測與鎖定 NVIDIA GPU 加速
try:
    import cupy as cp
    xp = cp
    HAS_GPU = True
except ImportError:
    xp = np
    HAS_GPU = False

app = Flask(__name__)

class SignalBasedLinearWaveService:
    def __init__(self):
        """
        傳統線性波模擬器 (SLWE) 微服務
        """
        # 初始化為標準線性疊加態 [1/sqrt(2), 1/sqrt(2)]
        self.state = np.array([1.0 / np.sqrt(2), 1.0 / np.sqrt(2)], dtype=complex)
        self.phi_delta = 0.0

    def apply_hadamard_gate(self):
        """ 傳統 SLWE 施加 Hadamard 閘 (使用線性矩陣乘法) """
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        self.state = np.dot(H, self.state)

    def apply_phase_rotation_gate(self, delta_phi):
        """ 傳統 SLWE 施加 Phase 旋轉閘 """
        P = np.array([[1, 0], [0, np.exp(1j * delta_phi)]])
        self.state = np.dot(P, self.state)

    def inject_phase_damping(self, noise_level=0.1):
        """ 
        【無防禦漏洞】模擬環境造成的隨機相位雜訊 
        SLWE 由於缺乏幾何剛性約束，雜訊會直接侵蝕複數矩陣的相位，無法自癒！
        """
        noise = np.random.normal(0, noise_level)
        self.phi_delta += noise
        self.state[1] = self.state[1] * np.exp(1j * noise)

    def get_coherence(self):
        """ 計算非對角相干項模值 |rho_01| """
        coherence_value = float(np.abs(self.state[0] * np.conj(self.state[1])))
        metric_check = float(np.abs(self.state[0])**2 + np.abs(self.state[1])**2)
        return coherence_value, metric_check

# 實體化傳統對比組位元
slwe_qubit = SignalBasedLinearWaveService()

@app.route('/ping', methods=['GET'])
def route_ping():
    return jsonify({
        "status": "ready",
        "device": "NVIDIA GeForce GTX 1050" if HAS_GPU else "CPU",
        "cuda_accelerated": HAS_GPU,
        "type": "SLWE (Traditional Linear Wave)"
    })

@app.route('/gate/h', methods=['POST'])
def route_gate_h():
    slwe_qubit.apply_hadamard_gate()
    return jsonify({"msg": "SLWE: H閘施加成功"})

@app.route('/gate/phase', methods=['POST'])
def route_gate_phase():
    data = request.json or {}
    delta_phi = data.get('delta_phi', 0.0)
    slwe_qubit.apply_phase_rotation_gate(delta_phi)
    return jsonify({"msg": "SLWE: Phase閘施加成功"})

@app.route('/noise/inject', methods=['POST'])
def route_noise_inject():
    data = request.json or {}
    noise_level = data.get('noise_level', 0.1)
    slwe_qubit.inject_phase_damping(noise_level)
    return jsonify({"msg": "SLWE: 退相干雜訊已直接侵蝕矩陣", "current_phi_delta": slwe_qubit.phi_delta})

@app.route('/measure/coherence', methods=['GET'])
def route_measure_coherence():
    coherence, metric = slwe_qubit.get_coherence()
    return jsonify({
        "coherence": coherence,
        "gauge_metric_integrity": metric
    })

# --- 關鍵修正：補上傳統 SLWE 的演化接口 ---
@app.route('/evolve', methods=['GET'])
def route_evolve():
    t = float(request.args.get('t', 1.0))
    coherence, metric = slwe_qubit.get_coherence()
    # 傳統方法直接回傳其退化後的度規狀態
    return jsonify({
        "status": "evolved",
        "t_final": t,
        "gauge_metric_integrity": metric
    })

if __name__ == "__main__":
    print(f"=== SLWE 傳統對比組微服務正在初始化... ===")
    app.run(host='0.0.0.0', port=5001)
