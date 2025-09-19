import subprocess, os, uuid, requests
from config import TMP_DIR

def download_file(url: str) -> str:
    fn = os.path.join(TMP_DIR, f"in_{uuid.uuid4().hex}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(fn, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    return fn

def to_wav_mono_16k(in_path: str) -> str:
    out = f"{in_path}.wav"
    cmd = [
        "ffmpeg", "-y", "-i", in_path,
        "-ac", "1", "-ar", "16000", "-f", "wav", out
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out