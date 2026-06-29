# ==============================================================================
# CLASSICAL SIGNAL-BASED LINEAR WAVE EQUATION (SLWE) BENCHMARK NODE CONTAINER
# BASE IMAGE: Leveraging the official NVIDIA CUDA 11.8 runtime on Ubuntu 22.04 LTS
# to ensure full architectural compatibility with baseline GPU hardware.
# ==============================================================================
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# ==============================================================================
# ENVIRONMENT SANITIZATION & LOGGING OPTIMIZATION
# PYTHONUNBUFFERED=1 forces standard output and error streams to be unbuffered,
# ensuring container log telemetry is transmitted to host monitors instantly.
# ==============================================================================
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_PORT=3000

# ==============================================================================
# CORE SYSTEM DEPENDENCIES
# Synchronize package repositories and establish the core Python3 execution 
# runtime. Installs python-is-python3 to resolve internal execution symlinks.
# ==============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# SCIENTIFIC & HIGH-CONCURRENCY ASGI WEBSERVER STACK
# Upgrades pip infrastructure and deploys the identical dependency manifest
# used in the HSQ core to guarantee computational equivalence across node matrices.
# ==============================================================================
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
    numpy \
    scipy \
    cupy-cuda11x \
    redis \
    fastapi \
    pydantic \
    uvicorn

# ==============================================================================
# CONTAINER ENVIRONMENT ANCHORING
# Define and instantiate the strict operating folder within the sandboxed runtime.
# ==============================================================================
WORKDIR /app

# ==============================================================================
# SOURCE CODE TRANSLATION & DECOUPLING
# Inject the classical signal benchmark solver backend into the container topology.
# ==============================================================================
COPY slwe_local.py /app/

# ==============================================================================
# NETWORKING BOUNDARY INTERFACE
# Broadcast and expose the localized runtime daemon communication port.
# ==============================================================================
EXPOSE 3000

# ==============================================================================
# HIGH-CONCURRENCY LIFECYCLE CONTROLLER (THE ASGI BREAKTHROUGH)
# Launches the Uvicorn production server to handle asynchronous network ingestion.
# Threads and tasks are dynamically dispatched into safe execution layers,
# mitigating CPU context switching overheads without fracturing CUDA Contexts.
# ==============================================================================
CMD ["uvicorn", "slwe_local:app", "--host", "0.0.0.0", "--port", "3000"]
