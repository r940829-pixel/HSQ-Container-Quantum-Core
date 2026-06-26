# ==============================================================================
# BASE IMAGE CONFIGURATION
# Leveraging the official NVIDIA CUDA 11.8 runtime on Ubuntu 22.04 LTS to 
# ensure full architectural compatibility with baseline GPU hardware and stable
# pass-through computing via the NVIDIA Container Toolkit.
# ==============================================================================
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# ==============================================================================
# ENVIRONMENT SANITIZATION
# Suppress interactive dialog prompts during the apt-get package installation 
# pipeline to enable fully automated and unattended DevOps container orchestration.
# ==============================================================================
ENV DEBIAN_FRONTEND=noninteractive

# ==============================================================================
# CORE SYSTEM DEPENDENCIES
# Synchronize package repositories and establish the core Python3 execution 
# runtime along with the pip package management infrastructure.
# Cache layers are aggressively purged to enforce a lightweight footprint.
# ==============================================================================
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# SCIENTIFIC & HIGH-CONCURRENCY ASYNCHRONOUS WEBSERVER STACK
# Provisioning scientific computing layers (NumPy), GPU-accelerated parallel 
# matrix engines (CuPy explicitly compiled for CUDA 11.x platforms), the 
# Redis client driver for non-local tensor side-talk, and replacing the 
# single-threaded Flask daemon with Gunicorn + Gevent high-performance 
# asynchronous co-routine WSGI engine to mitigate CPU context switching overheads.
# ==============================================================================
RUN pip3 install --no-cache-dir numpy cupy-cuda11x flask redis gunicorn gevent

# ==============================================================================
# CONTAINER ENVIRONMENT ANCHORING
# Define and instantiate the strict operating folder within the sandboxed 
# container runtime topology.
# ==============================================================================
WORKDIR /app

# ==============================================================================
# SOURCE CODE TRANSLATION & DECOUPLING
# Inject the microscopic physics engine backend script into the current active 
# hardware manifest layer.
# ==============================================================================
COPY hsq_qubit.py /app/

# ==============================================================================
# NETWORKING BOUNDARY INTERFACE
# Broadcast and expose the localized runtime daemon communication port to the 
# host loopback channel (allocated from Port 5011 onwards by the orchestrator).
# ==============================================================================
EXPOSE 5000

# ==============================================================================
# HIGH-CONCURRENCY LIFECYCLE CONTROLLER (THE CPU-BOUND BREAKTHROUGH)
# Initiates the WSGI application manager with 4 parallel workers bound to an 
# asynchronous greenlet-driven event loop (gevent), effectively shielding the 
# host OS from classical I/O blockades and multi-thread context-switch exhaustion.
# ==============================================================================
CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:5000", "app:app"]
