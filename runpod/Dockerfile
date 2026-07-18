# Custom Faster Whisper worker — same CUDA base as RunPod Hub worker
# (avoids runpod/base NVIDIA entrypoint exit-1 on modern hosts)
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash
WORKDIR /

RUN rm -f /etc/apt/sources.list.d/*.list \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        python3.10 python3-pip python3.10-venv \
        ffmpeg ca-certificates curl \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir \
        faster-whisper==1.1.0 \
        "runpod>=1.10.1" \
        httpx==0.27.0

COPY whisper_config.py /whisper_config.py
COPY handler.py /handler.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV WHISPER_MODEL=large-v3
ENV WHISPER_DEVICE=cuda
ENV WHISPER_COMPUTE=float16
ENV PYTHONUNBUFFERED=1

# Critical: do not inherit NVIDIA entrypoint (driver check → exit 1)
ENTRYPOINT []
CMD ["/start.sh"]
