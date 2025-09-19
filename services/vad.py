import webrtcvad
import collections
import contextlib
import wave
from typing import List, Tuple

_sr = 16000  
_frame_ms = 30  
_vad = webrtcvad.Vad(2)  

def read_wav(path: str) -> tuple[bytes, int]:
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        if wf.getframerate() != _sr or wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("WAV must be 16kHz, 16-bit PCM, mono")
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, wf.getframerate()

def frame_generator(frame_duration_ms: int, audio: bytes, sample_rate: int):
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)  
    offset = 0
    while offset + n < len(audio):
        yield audio[offset:offset + n]
        offset += n

def vad_collector(sample_rate: int, frame_duration_ms: int,
                  padding_duration_ms: int, vad: webrtcvad.Vad, audio: bytes):
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False
    voiced_frames = []
    segments = []
    frame_duration_s = frame_duration_ms / 1000.0
    frame_index = 0
    start_time = None

    for frame in frame_generator(frame_duration_ms, audio, sample_rate):
        is_speech = vad.is_speech(frame, sample_rate)
        t = frame_index * frame_duration_s
        frame_index += 1

        if not triggered:
            if is_speech:
                triggered = True
                start_time = t
        else:
            if not is_speech:
                triggered = False
                segments.append((start_time, t))
                start_time = None

    if triggered and start_time is not None:
        segments.append((start_time, frame_index * frame_duration_s))

    return segments

def speech_timestamps(wav_path: str, threshold: float = 0.5) -> List[Tuple[float, float]]:
    audio, sr = read_wav(wav_path)
    if sr != _sr:
        raise ValueError("Input wav must be 16kHz mono PCM")
    segments = vad_collector(sr, _frame_ms, 300, _vad, audio)
    return segments