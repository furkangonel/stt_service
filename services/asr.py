from faster_whisper import WhisperModel
from typing import List, Dict, Any
from config import ASR_MODEL, ASR_DEVICE, ASR_COMPUTE_TYPE

_model = WhisperModel(ASR_MODEL, device=ASR_DEVICE, compute_type=ASR_COMPUTE_TYPE)

def transcribe(path_wav: str, language: str = "tr") -> Dict[str, Any]:
    # vad_filter: filter out small noises, return segments with timestamps
    segments, info = _model.transcribe(
        path_wav,
        language=language,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=200)
    )

    out_segments = []
    full_text = []
    for seg in segments:
        out_segments.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text.strip(),
            "avg_logprob": getattr(seg, "avg_logprob", None)
        })
        full_text.append(seg.text.strip())
    return {
        "language": info.language or language,
        "segments": out_segments,
        "text": " ".join(full_text).strip()
    }