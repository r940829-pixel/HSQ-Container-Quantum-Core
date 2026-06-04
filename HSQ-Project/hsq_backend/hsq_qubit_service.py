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

class HilbertSpaceSpinorQuasiparticleService:
    def __init__(self):
        """
        封裝單顆 HSQ 準粒子的物理與自旋特徵
        """
        self.omega = 2.0   # 內徵頻率
        self.sigma = 1.0   # 波包空間寬度
        self.vg = 1.0      # 群速度
        
        # 初始狀態設為基態 |0> (a=1, b=0)
        self.a = 1.0
        self.b = 0.0
        self.theta = 0.0
        self.phi = 0.0
        self.phi_delta = 0.0  # 局域累積雜訊相位

    def enforce_gauge_protection(self):
        """ 【幾何規範防禦】強行投影回 a^2 + b^2 = 1 """
        norm = np.sqrt(np.abs(self.a)**2 + np.abs(self.b)**2)
        if norm > 0:
            self.a /= norm
            self.b /= norm

    def apply_hadamard_gate(self):
        """ 施加局域 Hadamard 閘 """
        self.theta = np.pi / 2
        self.phi = 0.0
        self.a = 1.0 / np.sqrt(2)
        self.b = 1.0 / np.sqrt(2)
        self.enforce_gauge_protection()

    def apply_phase_rotation_gate(self, delta_phi):
        """ 施加局域相位旋轉閘 """
        self.phi += delta_phi
        self.b = self.b * np.exp(1j * delta_phi)
        self.enforce_gauge_protection()

    def inject_phase_damping(self, noise_level=0.1):
        """ 模擬環境造成的局域退相干雜訊 """
        noise = np.random.normal(0, noise_level)
        self.phi_delta += noise
        self.enforce_gauge_protection()

    def compute_current_xi(self, t=1.0):
        """ 求解當前時空網格上的 xi 波動函數 """
        x_grid = xp.linspace(-10, 10, 500)
        envelope = (1.0 / (xp.pi * self.sigma**2))**0.25 * xp.exp(-((x_grid - self.vg * t)**2) / (2 * self.sigma**2))
        spinor_phase = (self.a + self.b) * self.omega * t + (self.a * self.theta + self.b * self.phi - self.phi_delta) * x_grid
        xi = envelope * xp.exp(1j * spinor_phase)
        
        if HAS_GPU:
            return cp.asnumpy(xi)
        return xi

# 實體化這顆活在容器裡的虛擬量子位元晶片
hsq_qubit = HilbertSpaceSpinorQuasiparticleService()

@app.route('/ping', methods=['GET'])
def route_ping():
    return jsonify({
        "status": "ready",
        "device": "NVIDIA GeForce GTX 1050" if HAS_GPU else "CPU",
        "cuda_accelerated": HAS_GPU
    })

@app.route('/gate/h', methods=['POST'])
def route_gate_h():
    hsq_qubit.apply_hadamard_gate()
    return jsonify({"msg": "Hadamard 閘施加成功", "a": float(np.abs(hsq_qubit.a)), "b": float(np.abs(hsq_qubit.b))})

@app.route('/gate/phase', methods=['POST'])
def route_gate_phase():
    data = request.json or {}
    delta_phi = data.get('delta_phi', 0.0)
    hsq_qubit.apply_phase_rotation_gate(delta_phi)
    return jsonify({"msg": "Phase 旋轉閘施加成功", "phi": float(hsq_qubit.phi)})

@app.route('/noise/inject', methods=['POST'])
def route_noise_inject():
    data = request.json or {}
    noise_level = data.get('noise_level', 0.1)
    hsq_qubit.inject_phase_damping(noise_level)
    return jsonify({"msg": "退相干雜訊已注入", "current_phi_delta": float(hsq_qubit.phi_delta)})

@app.route('/measure/coherence', methods=['GET'])
def route_measure_coherence():
    coherence_value = float(np.abs(hsq_qubit.a * np.conj(hsq_qubit.b)))
    gauge_check = float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2)
    return jsonify({
        "coherence": coherence_value,
        "gauge_metric_integrity": gauge_check
    })

# --- 關鍵修正：補上演算法需要的演化接口 ---
@app.route('/evolve', methods=['GET'])
def route_evolve():
    t = float(request.args.get('t', 1.0))
    # 呼叫物理引擎求解 xi 函數
    hsq_qubit.compute_current_xi(t=t)
    # 回傳度規狀態供前端繪圖判斷
    return jsonify({
        "status": "evolved",
        "t_final": t,
        "gauge_metric_integrity": float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2)
    })

if __name__ == "__main__":
    print(f"=== HSQ 單位元網路微服務正在初始化... ===")
    app.run(host='0.0.0.0', port=5000)
