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
        封裝單顆 HSQ 準粒子的物理與自旋特徵（幾何規範自癒防禦組）
        """
        # --- 變數全面更新：對齊我們之前定義好的時空場係數 ---
        self.omega_L = 2.0
        self.omega_R = 2.0
        self.k_L = 1.2
        self.k_R = -1.2
        
        self.sigma = 2.0   # 初始波包空間寬度 sigma_0
        self.vg = 0.8      # 群速度 v_g
        self.alpha = 0.1   # 包絡動態時空擴散係數
        self.current_step = 0
        
        # 初始狀態設為基態 |0> (a=1, b=0)
        self.a = 1.0 + 0j
        self.b = 0.0 + 0j
        self.theta = 0.0
        self.phi = 0.0
        self.k_delta = 0.0  # 🔥 累積雜訊相位名稱完美對齊為 k_delta

    def enforce_gauge_protection(self):
        """ 【幾何規範防禦】強行投影回 |a|^2 + |b|^2 = 1 捍衛希伯爾特流形剛性 """
        norm = np.sqrt(np.abs(self.a)**2 + np.abs(self.b)**2)
        if norm > 1e-6:
            self.a /= norm
            self.b /= norm

    def apply_hadamard_gate(self):
        """ 施加局域 Hadamard 閘 """
        self.theta = np.pi / 2
        self.phi = 0.0
        # 標準 2x2 麼正變換矩陣作用
        new_a = (1.0 / np.sqrt(2)) * self.a + (1.0 / np.sqrt(2)) * self.b
        new_b = (1.0 / np.sqrt(2)) * self.a - (1.0 / np.sqrt(2)) * self.b
        self.a, self.b = new_a, new_b
        self.enforce_gauge_protection()

    def apply_phase_rotation_gate(self, delta_phi):
        """ 施加局域相位旋轉閘 """
        self.phi += delta_phi
        self.b = self.b * np.exp(1j * delta_phi)
        self.enforce_gauge_protection()

    def inject_phase_damping(self, noise_level=0.1):
        """ 模擬環境造成的局域退相干雜訊 """
        noise = np.random.normal(0, noise_level)
        self.k_delta += noise  # 累加至環境波數雜訊項目
        self.enforce_gauge_protection()

    def compute_current_xi(self, t=1.0):
        """ 
        求解當前時空網格上的 xi 波動函數
        更新機制：採用更新後的物理參數進行投影
        """
        x_grid = xp.linspace(-20, 20, 500)
        
        # 1. 提取純實數的局域暫存器期望值權重 (防止複數相位直接乘網格導致指數大爆炸)
        weight_a = float(np.abs(self.a)**2)
        weight_b = float(np.abs(self.b)**2)
        w_total = weight_a + weight_b + 1e-9
        w_a, w_b = weight_a / w_total, weight_b / w_total
        
        # 2. 計算融入擴散項的時空高斯包絡外殼
        current_sigma = np.sqrt(self.sigma**2 + self.alpha * t)
        envelope_a = xp.exp(-((x_grid + self.vg * t)**2) / (2 * current_sigma**2))
        envelope_b = xp.exp(-((x_grid - self.vg * t)**2) / (2 * current_sigma**2))
        envelope = envelope_a * w_a + envelope_b * w_b
        
        # 3. 求解對齊定義的微觀總時空相位角 Theta(x,t)
        time_phase = (w_a * self.omega_L + w_b * self.omega_R) * t
        space_phase = (w_a * self.k_L + w_b * self.k_R - self.k_delta) * x_grid
        spinor_phase = time_phase + space_phase
        
        # 4. 疊加演化流形
        xi = envelope * (self.a + self.b) * xp.exp(1j * spinor_phase)
        
        # 5. 計算巨觀歸一化機率密度 P(x) = |xi|^2
        prob = xp.abs(xi)**2
        total_sum = float(xp.sum(prob))
        if total_sum > 0:
            prob = prob / total_sum
            
        if HAS_GPU:
            return [float(v) for v in cp.asnumpy(prob).flatten()]
        return [float(v) for v in prob.flatten()]

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
    return jsonify({"msg": "退相干雜訊已注入", "current_k_delta": float(hsq_qubit.k_delta)})

@app.route('/measure/coherence', methods=['GET'])
def route_measure_coherence():
    coherence_value = float(np.abs(hsq_qubit.a * np.conj(hsq_qubit.b)))
    gauge_check = float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2)
    return jsonify({
        "coherence": coherence_value,
        "gauge_metric_integrity": gauge_check
    })

# --- 完美對齊演算法要求的時空場推進接口 ---
@app.route('/evolve', methods=['POST', 'GET'])
def route_evolve():
    # 支援 GET query 與 POST json 雙棲，最大化前端相容性
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        noise_level = float(data.get('noise', 0.0))
        hsq_qubit.current_step += 1
        t = hsq_qubit.current_step * 0.1
    else:
        t = float(request.args.get('t', 1.0))
        noise_level = float(request.args.get('noise', 0.0))
        
    if noise_level > 0:
        hsq_qubit.inject_phase_damping(noise_level)
        
    # 求解符合定義係數的 500 點空間機率分佈
    prob_dist = hsq_qubit.compute_current_xi(t=t)
    
    # 完美回傳前端需要的關鍵鍵值對 "probability_density"
    return jsonify({
        "status": "evolved",
        "t_final": t,
        "gauge_metric_integrity": float(np.abs(hsq_qubit.a)**2 + np.abs(hsq_qubit.b)**2),
        "probability_density": prob_dist
    })

if __name__ == "__main__":
    print(f"=== [HSQ 完備更新版微服務] 初始化成功，正在監聽 5000 埠口 ===")
    app.run(host='0.0.0.0', port=5000)
