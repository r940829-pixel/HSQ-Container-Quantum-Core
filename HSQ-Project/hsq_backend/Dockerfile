# 使用相容你 GTX 1050 且體積輕量穩定的官方 CUDA 運行時鏡像
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# 避免安裝互動式軟體包時卡住
ENV DEBIAN_FRONTEND=noninteractive

# 安裝 Python 核心與 pip 管理器
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 一鍵安裝數學運算庫與微服務通訊庫 (Flask)
RUN pip3 install --no-cache-dir numpy cupy-cuda11x flask

# 建立並定位容器內部工作資料夾
WORKDIR /app

# 將剛剛寫好的單位元服務程式碼複製進去
COPY hsq_qubit_service.py /app/

# 宣告對外開放的內部通訊埠
EXPOSE 5000

# 預設啟動命令
CMD ["python3", "hsq_qubit_service.py"]
