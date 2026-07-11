# ==============================================================================
# CLASSICAL SIGNAL-BASED LINEAR WAVE EQUATION (SLWE) BENCHMARK NODE CONTAINER
# BASE IMAGE: Leveraging the official NVIDIA CUDA 11.8 runtime on Ubuntu 22.04 LTS
# ==============================================================================
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# ==============================================================================
# ENVIRONMENT SANITIZATION & LOGGING OPTIMIZATION
# ==============================================================================
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_PORT=3000

# ==============================================================================
# CORE SYSTEM DEPENDENCIES
# ==============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# SCIENTIFIC & HIGH-CONCURRENCY WSGI PRODUCTION STACK
# ==============================================================================
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
    numpy \
    scipy \
    cupy-cuda11x \
    flask \
    gunicorn

# ==============================================================================
# CONTAINER ENVIRONMENT ANCHORING
# ==============================================================================
WORKDIR /app

# ==============================================================================
# SOURCE CODE TRANSLATION
# ==============================================================================
COPY slwe_local.py /app/

# ==============================================================================
# NETWORKING BOUNDARY INTERFACE
# ==============================================================================
EXPOSE 3000

# ==============================================================================

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "1", "--timeout", "120", "slwe_local:app"]
