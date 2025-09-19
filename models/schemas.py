from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class TranscribeRequest(BaseModel):
    audio_url: HttpUrl
    language: Optional[str] = "tr"
    expected_speakers: Optional[int] = None 

class Segment(BaseModel):
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    avg_logprob: Optional[float] = None

class TranscribeResponse(BaseModel):
    text: str
    language: str
    speakers: List[str]
    segments: List[Segment]

class HealthResponse(BaseModel):
    status: str
    asr_model: str
    device: str