FROM runpod/base:0.6.2-cuda12.1.0

RUN pip install --no-cache-dir \
    faster-whisper==1.1.0 \
    runpod==1.9.1 \
    httpx==0.27.0

COPY whisper_config.py /whisper_config.py
COPY handler.py /handler.py

ENV WHISPER_MODEL=large-v3
ENV WHISPER_DEVICE=cuda
ENV WHISPER_COMPUTE=float16

CMD ["python3", "-u", "/handler.py"]
