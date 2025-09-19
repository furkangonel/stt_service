# services/diarize.py
from typing import List, Dict, Any, Tuple
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
import soundfile as sf
from sklearn.cluster import KMeans

_encoder = VoiceEncoder()

def _cluster_embeddings_kmeans(embeds: np.ndarray, k: int) -> np.ndarray:
    if embeds.shape[0] < 2:
        return np.zeros((embeds.shape[0],), dtype=int)
    k = max(1, min(k, embeds.shape[0]))
    km = KMeans(n_clusters=k, n_init="auto", random_state=42)
    return km.fit_predict(embeds)

def diarize(wav_path: str, vad_segments: List[Tuple[float, float]],
            expected_speakers: int | None, max_spk: int) -> List[Dict[str, Any]]:

    y, sr = sf.read(wav_path)
    if y.ndim == 2:
        y = y.mean(axis=1)

    samples, times = [], []
    step = 0.5
    for (s, e) in vad_segments:
        t = s
        while t < e:
            s_samp = int(t * sr)
            e_samp = int(min(e, t + step) * sr)
            clip = y[s_samp:e_samp]
            if len(clip) < int(0.3 * sr):
                t += step; continue
            wav = preprocess_wav(clip, source_sr=sr)
            if len(wav) == 0:
                t += step; continue
            emb = _encoder.embed_utterance(wav)
            samples.append(emb)
            times.append((t, min(e, t + step)))
            t += step

    if not samples:
        return []

    embeds = np.vstack(samples)

    if expected_speakers and expected_speakers > 0:
        k = min(expected_speakers, embeds.shape[0])
    else:
        k = max(1, min(max_spk, embeds.shape[0]))

    labels = _cluster_embeddings_kmeans(embeds, k=k)

    # Combine consecutive same speakers
    diar = []
    cur_label = int(labels[0]); cur_start, cur_end = times[0]
    for i in range(1, len(labels)):
        if int(labels[i]) == cur_label and abs(times[i][0] - cur_end) < 0.6:
            cur_end = times[i][1]
        else:
            diar.append({"start": float(cur_start), "end": float(cur_end), "speaker": int(cur_label)})
            cur_label = int(labels[i]); cur_start, cur_end = times[i]
    diar.append({"start": float(cur_start), "end": float(cur_end), "speaker": int(cur_label)})

    # Human readable names
    uniq = sorted(list(set(d["speaker"] for d in diar)))
    spk_map = {i: f"SPEAKER_{i:02d}" for i in uniq}
    for d in diar:
        d["speaker"] = spk_map[d["speaker"]]
    return diar