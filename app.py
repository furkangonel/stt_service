from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from models.schemas import TranscribeRequest, TranscribeResponse, HealthResponse
from services.audio_io import download_file, to_wav_mono_16k
from services.asr import transcribe as asr_transcribe
from services.vad import speech_timestamps
from services.diarize import diarize
from services.align import assign_speakers, speakers_from_diar
from config import ASR_MODEL, ASR_DEVICE, DIAR_MAX_SPK
import shutil
import tempfile
import subprocess
import os

app = FastAPI(title="STT+Diarization Service", version="1.0")

ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",   # .mov
    "video/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",        # .mp3
    "audio/mp4",         # .m4a
    "audio/webm",
    "audio/ogg",
}
MAX_UPLOAD_MB = 1024  

@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "asr_model": ASR_MODEL, "device": ASR_DEVICE}

# ------- Ortak boru hattı yardımcıları

def _save_upload_to_tmp(upload: UploadFile) -> str:
    """
    It safely saves the incoming file to the temporary directory and returns the full path.
    """
   
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {upload.content_type}")

    length = None
    if upload.headers and "content-length" in upload.headers:
        try:
            length = int(upload.headers["content-length"])
        except Exception:
            pass
    if length and length > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (> {MAX_UPLOAD_MB} MB)")

    # simple extension generation
    suffix = ""
    ct = upload.content_type or ""
    if ct == "video/mp4":
        suffix = ".mp4"
    elif ct == "video/quicktime":
        suffix = ".mov"
    elif ct in ("audio/wav", "audio/x-wav"):
        suffix = ".wav"
    elif ct == "audio/mpeg":
        suffix = ".mp3"
    elif ct == "audio/mp4":
        suffix = ".m4a"
    elif ct in ("video/webm", "audio/webm"):
        suffix = ".webm"
    elif ct == "audio/ogg":
        suffix = ".ogg"

    fd, tmp_path = tempfile.mkstemp(prefix="upload_", suffix=suffix)
    os.close(fd)
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(upload.file, out)
    finally:
        try:
            upload.file.close()
        except:
            pass
    return tmp_path

def _process_local_media_file(local_path: str, language: str, expected_speakers: int | None):
    """
    Takes existing file path, converts to WAV 16k and produces the result with the existing pipeline.
    """

    try:
        wav = to_wav_mono_16k(local_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"FFmpeg convert failed: {e}")

    # 2) ASR
    asr = asr_transcribe(wav, language or "tr")

    # 3) VAD -> Diarization
    vad = speech_timestamps(wav)  # [(start,end), ...]
    exp = expected_speakers if (expected_speakers and expected_speakers > 0) else None
    diar = diarize(wav, vad, exp, DIAR_MAX_SPK)

    # 4) Assign speakers to ASR segments
    segs = assign_speakers(asr["segments"], diar)
    speakers = speakers_from_diar(diar) or ["SPEAKER_00"]

    # 5) response
    resp = {
        "text": asr["text"],
        "language": asr["language"],
        "speakers": speakers,
        "segments": segs
    }

    # 6) temp cleanup
    try:
        os.remove(wav)
    except:
        pass
    return resp

# ------- transcript with URL
@app.post("/v1/stt/transcribe", response_model=TranscribeResponse)
def stt(req: TranscribeRequest):
    # 1) download + wav 16k mono
    try:
        in_path = download_file(req.audio_url)
        wav = to_wav_mono_16k(in_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio fetch/convert failed: {e}")

    # 2) ASR
    asr = asr_transcribe(wav, req.language)

    # 3) VAD -> Diarization
    vad = speech_timestamps(wav)  # [(start,end), ...]
    diar = diarize(wav, vad, req.expected_speakers, DIAR_MAX_SPK)

    # 4) ASR segmentlerine konuşmacı ata
    segs = assign_speakers(asr["segments"], diar)
    speakers = speakers_from_diar(diar) or ["SPEAKER_00"]

    # 5) response
    resp = {
        "text": asr["text"],
        "language": asr["language"],
        "speakers": speakers,
        "segments": segs
    }

    # 6) temp cleanup
    try:
        os.remove(in_path)
        os.remove(wav)
    except:
        pass

    return resp

# ------- transcript with Multipart upload 
@app.post("/v1/stt/upload", response_model=TranscribeResponse)
async def stt_upload(
    file: UploadFile = File(..., description="mp4/mov/wav/mp3 gibi medya dosyası"),
    language: str = Form("tr"),
    expected_speakers: int | None = Form(None),
):
    """
    Swagger'da dosya seçerek yükleme yap ve aynı JSON çıktıyı al.
    """
    # 1) Save file in temporary directory
    local_path = _save_upload_to_tmp(file)

    try:
        # 2) Run the common pipeline
        resp = _process_local_media_file(local_path, language, expected_speakers)
        return resp
    finally:
        # 3) Clear the uploaded raw file
        try:
            os.remove(local_path)
        except:
            pass


@app.websocket("/ws/stt/stream")
async def ws_stream(ws: WebSocket):
    await ws.accept()
    buffer = bytearray()
    try:
        while True:
            data = await ws.receive_bytes()
            buffer.extend(data)
           
            if len(buffer) > 16000*2*5:  
                tmp_in = "/tmp/live_chunk.raw"
                tmp_wav = "/tmp/live_chunk.wav"
                with open(tmp_in, "wb") as f:
                    f.write(buffer)
                subprocess.run(
                    ["ffmpeg","-y","-f","s16le","-ar","16000","-ac","1","-i",tmp_in,tmp_wav],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                asr = asr_transcribe(tmp_wav, "tr")
                await ws.send_json({"partial": True, "text": asr["text"], "segments": asr["segments"]})
                buffer.clear()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await ws.send_json({"error": str(e)})
    finally:
        await ws.close()