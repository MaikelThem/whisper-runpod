"""Parámetros de faster-whisper orientados a máxima precisión (español / clases)."""
import os


def _float(name, default):
    return float(os.getenv(name, str(default)))


def _int(name, default):
    return int(os.getenv(name, str(default)))


def _bool(name, default=False):
    value = os.getenv(name, str(default)).lower()
    return value in ("1", "true", "yes", "on")


INITIAL_PROMPTS = {
    "es": (
        "Transcripción en español rioplatense. Puntuación, tildes, nombres propios, "
        "artículos de ley y términos técnicos correctamente escritos."
    ),
    "en": "Transcription in English with proper punctuation, capitalization, and technical terms.",
    "pt": "Transcrição em português com pontuação e acentuação corretas.",
}


def resolve_language(language):
    if not language or language == "auto":
        return None
    return language.split("-")[0].lower()


def get_initial_prompt(language):
    lang = resolve_language(language)
    if not lang:
        return None
    return INITIAL_PROMPTS.get(lang)


def get_transcribe_kwargs(language, word_timestamps=False):
    """Opciones de decodificación para alta precisión (beam search + VAD + temp 0)."""
    lang = resolve_language(language)
    kwargs = {
        "language": lang,
        "beam_size": _int("WHISPER_BEAM_SIZE", 10),
        "best_of": _int("WHISPER_BEST_OF", 5),
        "patience": _float("WHISPER_PATIENCE", 2.0),
        "length_penalty": _float("WHISPER_LENGTH_PENALTY", 1.0),
        "repetition_penalty": _float("WHISPER_REPETITION_PENALTY", 1.05),
        "no_repeat_ngram_size": _int("WHISPER_NO_REPEAT_NGRAM", 3),
        "temperature": [0.0],
        "compression_ratio_threshold": _float("WHISPER_COMPRESSION_RATIO", 2.4),
        "log_prob_threshold": _float("WHISPER_LOG_PROB", -1.0),
        "no_speech_threshold": _float("WHISPER_NO_SPEECH", 0.6),
        "condition_on_previous_text": True,
        "word_timestamps": word_timestamps,
        "initial_prompt": get_initial_prompt(language),
    }

    if _bool("WHISPER_VAD", True):
        kwargs["vad_filter"] = True
        kwargs["vad_parameters"] = {
            "min_silence_duration_ms": _int("WHISPER_VAD_MIN_SILENCE", 500),
            "speech_pad_ms": _int("WHISPER_VAD_SPEECH_PAD", 400),
        }

    return kwargs


def join_segment_text(segments):
    parts = []
    for segment in segments:
        text = (segment.text or "").strip()
        if text:
            parts.append(text)
    return " ".join(parts).strip()
