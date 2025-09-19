import os

ASR_MODEL = os.getenv("ASR_MODEL", "medium")      
ASR_DEVICE = os.getenv("ASR_DEVICE", "cpu")      
ASR_COMPUTE_TYPE = os.getenv("ASR_COMPUTE_TYPE", "int8")  
DIAR_MAX_SPK = int(os.getenv("DIAR_MAX_SPK", "8"))       
VAD_FRAME_MS = int(os.getenv("VAD_FRAME_MS", "30"))       

TMP_DIR = os.getenv("TMP_DIR", "/tmp")