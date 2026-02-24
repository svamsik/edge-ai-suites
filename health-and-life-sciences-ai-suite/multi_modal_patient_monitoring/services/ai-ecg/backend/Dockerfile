
FROM python:3.12-slim

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

WORKDIR /app

# ----------------------------------------------------------------------------
# System dependencies (OpenVINO + OpenCV GPU requirements)
# ----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1 \
    libnuma1 \
    ocl-icd-libopencl1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------------------------
# Install Python dependencies
# ----------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------------
# GPU Driver Installation (Same as rppg)
# ----------------------------------------------------------------------------
ARG INSTALL_DRIVER_VERSION="25.31.34666"

COPY scripts/install_ubuntu_gpu_drivers.sh /tmp/install_gpu_drivers.sh
RUN chmod +x /tmp/install_gpu_drivers.sh
RUN /tmp/install_gpu_drivers.sh

# Intel NPU user-space drivers (linux-npu-driver + Level Zero)
COPY ./scripts/install_ubuntu_npu_drivers.sh /tmp/install_npu_drivers.sh
RUN chmod +x /tmp/install_npu_drivers.sh
RUN /tmp/install_npu_drivers.sh

RUN apt-get clean && rm -rf /tmp/install_gpu_drivers.sh /tmp/install_npu_drivers.sh && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/* && rm -rf /root/.cachetmp/*

# ----------------------------------------------------------------------------
# Copy application code
# ----------------------------------------------------------------------------
COPY . .

ENV PYTHONPATH=/app

# Default AI-ECG service port (can be overridden via AI_ECG_PORT)
ENV AI_ECG_PORT=8101

EXPOSE 8101

# ----------------------------------------------------------------------------
# Run app - ensure models are downloaded first; port driven by AI_ECG_PORT
# ----------------------------------------------------------------------------
CMD ["sh", "-c", "python scripts/download_assets.py && uvicorn app:app --host 0.0.0.0 --port ${AI_ECG_PORT:-8101}"]