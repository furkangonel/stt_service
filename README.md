# 🗣️ STT Service (FastAPI + faster-whisper)

This project is a simple **Speech-to-Text** service developed using **FastAPI**. Audio files are converted to text using the `faster-whisper` model. 

---

## 🚀 Features
- 🎤 You can send the audio file via the **API endpoint** and receive a transcript. 
- ⚡ Fast and accurate transcription with **faster-whisper**. 
- 🔊 Supports formats such as `wav`, `mp3`, `flac`. 
- 📦 Easy installation in Docker or a virtual environment. 

---

## Screen Shots

![STT Service Swagger Interface](https://raw.githubusercontent.com/furkangonel/stt_service/assets/swagger_scene.png)

![Upload Endpoint](https://raw.githubusercontent.com/furkangonel/stt_service/assets/upload_endpoint.png)

![Response](https://raw.githubusercontent.com/furkangonel/stt_service/assets/response.png)

---

## 📂 Setup

### 1. clone repository
```bash
git clone https://github.com/kullanici/stt-service.git
cd stt-service
```

### 2. Create and activate virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
```

### 3. Install required dependencies
```bash 
pip install -r requirements.txt
```

### ▶️ Run service
```bash 
uvicorn app:app --reload
```

