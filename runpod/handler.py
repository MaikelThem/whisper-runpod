import os
import sys
import traceback
import tempfile
from urllib.parse import urlparse

import httpx
import runpod

from whisper_config import get_transcribe_kwargs, join_segment_text

MODEL_SIZE = os.getenv("WHISPER_MODEL", "large-v3")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE", "float16")

_model = None


def _json_float(value):
    if value is None:
        return 0.0
    return float(value)


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        print(f"Cargando Whisper {MODEL_SIZE} en {DEVICE} ({COMPUTE_TYPE})...", flush=True)
        _model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            num_workers=int(os.getenv("WHISPER_NUM_WORKERS", "4")),
        )
        print("Modelo listo", flush=True)
    return _model


def _suffix_from_url(url):
    path = urlparse(url).path.lower()
    extensions = (
        ".mp3", ".wav", ".wave", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".flac", ".wma",
        ".amr", ".aiff", ".aif", ".caf", ".au", ".mka", ".ac3", ".eac3", ".dts", ".mp2",
        ".mpc", ".ape", ".tta", ".wv", ".ra", ".ram", ".mid", ".midi", ".m4b", ".m4p", ".m4r",
        ".mp4", ".m4v", ".mov", ".qt", ".mkv", ".avi", ".wmv", ".flv", ".webm", ".mpeg", ".mpg",
        ".mpe", ".mpv", ".m2v", ".ts", ".mts", ".m2ts", ".vob", ".ogv", ".3gp", ".3g2", ".asf",
        ".wm", ".rm", ".rmvb", ".divx", ".f4v", ".swf", ".dat", ".mod", ".tod", ".mxf", ".insv",
    )
    for ext in extensions:
        if path.endswith(ext):
            return ext
    return ".mp3"


def handler(job):
    input_data = job.get("input") or {}

    if input_data.get("ping"):
        return {
            "pong": True,
            "model": MODEL_SIZE,
            "quality": "max",
            "beam_size": int(os.getenv("WHISPER_BEAM_SIZE", "10")),
        }

    url = input_data.get("url") or input_data.get("audio")
    language = input_data.get("language", "es")
    word_timestamps = bool(input_data.get("word_timestamps", False))

    if not url:
        return {"error": "url es requerida"}

    tmp_path = None
    try:
        with httpx.Client(timeout=300, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            audio_data = resp.content

        if len(audio_data) < 100:
            return {"error": f"audio demasiado chico ({len(audio_data)} bytes)"}

        suffix = _suffix_from_url(url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        model = get_model()
        transcribe_kwargs = get_transcribe_kwargs(language, word_timestamps=word_timestamps)
        segments, info = model.transcribe(tmp_path, **transcribe_kwargs)
        segments_list = list(segments)
        text = join_segment_text(segments_list)
        segments_out = [
            {
                "start": _json_float(s.start),
                "end": _json_float(s.end),
                "text": (s.text or "").strip(),
            }
            for s in segments_list
            if (s.text or "").strip()
        ]

        if not text:
            return {"error": "transcripción vacía (sin voz detectada)"}

        return {
            "text": text,
            "language": str(info.language or language or ""),
            "segments": segments_out,
            "duration": _json_float(info.duration),
            "quality": "max",
        }

    except Exception as e:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr, flush=True)
        return {"error": str(e)[:500]}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


if __name__ == "__main__":
    try:
        print(
            f"whisper-runpod ready model={MODEL_SIZE} device={DEVICE} compute={COMPUTE_TYPE}",
            flush=True,
        )
        runpod.serverless.start({"handler": handler})
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        # Keep container alive briefly so RunPod logs capture the traceback
        import time

        time.sleep(30)
        raise
