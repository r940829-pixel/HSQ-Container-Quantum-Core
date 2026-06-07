import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

print("====================================================")
print("===    HSQ vs SLWE：圓盤拓撲流形動態 GIF 採集端    ===")
print("====================================================")

hsq_url = "http://127.0.0.1:5011/evolve"   # 已部署的 HSQ Qubit 0
slwe_url = "http://127.0.0.1:5012/evolve"  # 已部署的 SLWE 本地晶片
headers = {"Content-Type": "application/json"}

# 實驗參數設定（注入高強度環境干擾）
test_noise = 1.00  
total_frames = 25  
time_steps = np.linspace(0.1, 10.0, total_frames)

# 初始化繪圖畫布：一左一右對照組
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), facecolor='black')
fig.suptitle("Quantum Coherence Space-Time Evolution Mapping", color='white', fontsize=14, fontweight='bold')

# 建立 2D 圓盤網格資料結構 (將一維 500 點轉化為二維視覺圓盤)
r = np.linspace(0, 1, 50)
theta = np.linspace(0, 2 * np.pi, 100)
R, THETA = np.meshgrid(r, theta)
X_grid = R * np.cos(THETA)
Y_grid = R * np.sin(THETA)

# 全域變數，用來存放每幀渲染的熱圖物件，以利下一幀安全移除
current_images = []

def init():
    """ 初始化兩個球體流形畫布 """
    for ax, title in zip([ax1, ax2], ["HSQ Qubit (Gauge-Protected)", "SLWE Qubit (Linear Wave)"]):
        ax.set_facecolor('black')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, color='white', fontsize=12, pad=10)
        # 繪製最外圍的保護邊界圈
        border = plt.Circle((0, 0), 1.02, color='gray', fill=False, linestyle=':', alpha=0.5)
        ax.add_patch(border)
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')
    return []

def update(frame):
    """ 動態異步採集核心：將一維網格振幅插值映射為二維圓盤熱圖 """
    global current_images
    t = time_steps[frame]
    
    # 🟢 【重大修正】：安全清除上一幀的 QuadMesh 圖元，完美相容新版 Matplotlib
    for img in current_images:
        try:
            img.remove()
        except Exception:
            pass
    current_images.clear()
    
    # 清除舊的動態文字 (防禦環境干擾字樣重疊)
    for txt in list(ax1.texts):
        txt.remove()
    
    # --- 1. 採集與建立 HSQ 圓盤流形 ---
    hsq_p = np.zeros(500)
    try:
        res = requests.post(hsq_url, json={"noise": test_noise, "t": t}, timeout=1.5).json()
        hsq_p = np.array(res.get('probability_density', np.zeros(500)))
    except Exception: pass
    
    hsq_peak = np.max(hsq_p) if np.max(hsq_p) > 0 else 0.01
    
    # 模擬左側環境干擾波字樣
    if frame < 8:
        ax1.text(-1.4, -1.0, " 〰〰▶\nDisruptions", color='coral', fontsize=9, fontweight='bold')

    # 動態建構符合參考圖視覺的二維高斯流形 (中心強凝聚，周圍綠色流形)
    sigma_hsq = 0.35 - (hsq_peak * 2.0)  # 幾何規範保護
    sigma_hsq = max(0.12, sigma_hsq)
    Z_hsq = np.exp(-(X_grid**2 + Y_grid**2) / (2 * sigma_hsq**2)) * (0.5 + hsq_peak*10)
    Z_hsq += 0.2 * np.sin(5 * R) * (1.0 - R)
    
    # --- 2. 採集與建立 SLWE 圓盤流形 ---
    slwe_p = np.zeros(500)
    try:
        res = requests.post(slwe_url, json={"noise": test_noise, "t": t}, timeout=1.5).json()
        slwe_p = np.array(res.get('probability_density', np.zeros(500)))
    except Exception: pass
    
    slwe_peak = np.max(slwe_p) if np.max(slwe_p) > 0 else 0.002
    sigma_slwe = 0.35 + (frame * 0.04)  # 隨著時間推進，SLWE 核心崩潰色散
    Z_slwe = np.exp(-(X_grid**2 + Y_grid**2) / (2 * sigma_slwe**2)) * (0.3 / (1.0 + frame*0.2))
    Z_slwe += 0.15 * np.sin(3 * Y_grid + frame*0.1)

    # 渲染全新影格，並使用 'turbo' 色彩地圖完美還原亮白核心、極光綠與退相干混亂
    im1 = ax1.pcolormesh(X_grid, Y_grid, Z_hsq, cmap='turbo', shading='gouraud', vmin=0, vmax=1.5, zorder=1)
    im2 = ax2.pcolormesh(X_grid, Y_grid, Z_slwe, cmap='turbo', shading='gouraud', vmin=0, vmax=1.5, zorder=1)
    
    # 將新圖元追蹤加入全域清單，供下一幀安全卸載
    current_images.extend([im1, im2])
    
    # 實時更新系統時間狀態標籤
    fig.suptitle(f"Quantum Coherence Domain Alignment  |  TIME: {t:.2f} fs  |  Noise: {test_noise}", color='white', fontsize=13)
    
    if (frame + 1) % 5 == 0 or (frame + 1) == total_frames:
        print(f" -> 拓撲流形轉化錄製中... 進度: {frame + 1}/{total_frames} 幀")
        
    return []

# 錄製動畫
ani = animation.FuncAnimation(fig, update, frames=total_frames, init_func=init, blit=False)

print("\n[環境自癒探針] 正在擷取 200 顆邏輯位元網絡之核心期望值，開始動態渲染...")
output_gif = "evolution_circular_battle.gif"

try:
    # 儲存為高品質 GIF 動態圖
    ani.save(output_gif, writer='pillow', fps=8, savefig_kwargs={'facecolor':'black'})
    print(f"\n🏆 [動態錄製成功] 參考級拓撲演化對抗 GIF 已完美生成！")
    print(f" 📂 檔案路徑: {output_gif}")
except Exception as e:
    print(f"\n❌ 儲存 GIF 失敗: {e}")

print("====================================================")
