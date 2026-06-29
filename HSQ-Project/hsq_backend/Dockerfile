# ==============================================================================
# HILBERT-SPACE SPINOR QUASIPARTICLE (HSQ) FASTAPI MICROSERVICE
# BASE IMAGE: Official NVIDIA CUDA 11.8 Runtime on Ubuntu 22.04 LTS
# ==============================================================================
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# ==============================================================================
# ENVIRONMENT ANCHORING & SANITIZATION
# ==============================================================================
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_PORT=5000

# ==============================================================================
# CORE SYSTEM DEPENDENCIES
# Establish the core Python3 execution runtime.
# ==============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# SCIENTIFIC & HIGH-CONCURRENCY ASYNCHRONOUS WEBSERVER STACK
# Provisioning scientific computing layers (NumPy, SciPy for matrix exponentials), 
# GPU-accelerated parallel matrix engines (CuPy), Redis driver, 
# and the FastAPI + Uvicorn asynchronous framework.
# ==============================================================================
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    numpy \
    scipy \
    cupy-cuda11x \
    redis \
    fastapi \
    pydantic \
    uvicorn

# ==============================================================================
# WORKSPACE INITIALIZATION
# ==============================================================================
WORKDIR /app

# Copy the HSQ microservice physics engine into the container topology
COPY hsq_qubit.py /app/

# Expose the designated local runtime communication port
EXPOSE 5000

# ==============================================================================
# LIFECYCLE CONTROLLER (THE FASTAPI/UVICORN BREAKTHROUGH)
# Initiates the ASGI application manager via Uvicorn.
# Running a single worker relies on FastAPI's native async event loop and 
# threadpool delegation, perfectly shielding the host OS from I/O blockades 
# without breaking the CUDA context or IBM Mutex locks.
# ==============================================================================
CMD ["uvicorn", "hsq_qubit:app", "--host", "0.0.0.0", "--port", "5000"]
