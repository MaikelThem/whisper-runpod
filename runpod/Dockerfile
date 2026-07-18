# Serverless worker: Faster Whisper (custom)
# Importante: limpiar ENTRYPOINT de NVIDIA (evita exit 1 por check de driver).
FROM runpod/base:0.6.2-cuda12.1.0

WORKDIR /

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    faster-whisper==1.1.0 \
    runpod==1.9.1 \
    httpx==0.27.0

COPY whisper_config.py /whisper_config.py
COPY handler.py /handler.py

ENV WHISPER_MODEL=large-v3
ENV WHISPER_DEVICE=cuda
ENV WHISPER_COMPUTE=float16
ENV PYTHONUNBUFFERED=1

# Anula /opt/nvidia/nvidia_entrypoint.sh del base CUDA
ENTRYPOINT []
CMD ["python3", "-u", "/handler.py"]
