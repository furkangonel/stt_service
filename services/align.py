from typing import List, Dict, Any

def _overlap(a_start, a_end, b_start, b_end):
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))

def assign_speakers(asr_segments: List[Dict[str, any]], diar_segments: List[Dict[str, any]]) -> List[Dict[str, any]]:
    # Assign the speaker with the most time overlap for each ASR sentence
    if not diar_segments:
        return [{**s, "speaker": "SPEAKER_00"} for s in asr_segments]

    with_spk = []
    for s in asr_segments:
        best_spk = None
        best_ol = 0.0
        for d in diar_segments:
            ol = _overlap(s["start"], s["end"], d["start"], d["end"])
            if ol > best_ol:
                best_ol = ol
                best_spk = d["speaker"]
        with_spk.append({**s, "speaker": best_spk or "SPEAKER_00"})
    return with_spk

def speakers_from_diar(diar_segments: List[Dict[str, any]]) -> list[str]:
    return sorted(list({d["speaker"] for d in diar_segments}))