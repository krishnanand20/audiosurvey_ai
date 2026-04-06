# AudioSurvey AI

**Status: Completed**

An AI-powered multilingual Interactive Voice Response (IVR) survey platform built for academic and public health field research. The system conducts fully automated telephone surveys in Kiswahili, targeting African refugee populations, using cloud telephony, neural speech synthesis, and a multi-stage ML audio processing pipeline.

---

## Overview

AudioSurvey AI automates the full lifecycle of a telephone survey — from scheduling outbound calls to transcribing, translating, and re-synthesizing participant responses in English — all managed through a secure web-based admin dashboard.

---

## Features

### Call Handling
- **Outbound calling** — scheduled batch calls to participant lists with retry logic
- **Inbound calling** — participants can call in and complete the survey
- **Conference calls** — admin can join active calls for live monitoring
- **Full-call audio recording** — complete call recordings stored per participant

### Survey Engine
- Multi-question IVR voice survey flow in Kiswahili
- Azure Neural Text-to-Speech for natural-sounding question delivery
- Configurable survey questions via `config.yaml`

### ML Processing Pipeline (4-stage)
1. **Noise Removal** — DeepFilterNet for audio pre-processing
2. **Transcription** — OpenAI Whisper for Kiswahili speech-to-text
3. **Translation** — Google Translate for Kiswahili → English
4. **English Audio Generation** — gTTS/Azure TTS for English audio output

### Admin Dashboard
- Secure login with JWT authentication
- Real-time participant tracking and call status
- Scheduled outbound call management
- Export survey results to structured Excel workbooks (`.xlsx`)
- Runtime status monitoring and background worker controls

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Telephony | Twilio Voice API |
| Speech Synthesis | Azure Cognitive Services (Neural TTS) |
| Speech Recognition | OpenAI Whisper |
| Noise Reduction | DeepFilterNet |
| Translation | Google Translate (googletrans) |
| Audio Fallback TTS | gTTS |
| Data Export | openpyxl (Excel) |
| Auth | PyJWT, scrypt (PBKDF2) |
| Scheduling | APScheduler (background_worker) |
| Tunnel (local dev) | ngrok |

---

## Project Structure

```
audiosurvey_ai/
├── app/
│   ├── twilio_handler.py     # Core IVR call routing and webhook handlers
│   ├── twilio_utils.py       # Twilio API helpers
│   ├── dashboard.py          # Admin dashboard routes
│   ├── auth.py               # Login, JWT, session management
│   ├── scheduler.py          # Outbound call scheduling
│   ├── background_worker.py  # Async ML pipeline processing
│   ├── audio_preprocess.py   # DeepFilterNet noise removal
│   ├── transcribe.py         # Whisper speech-to-text
│   ├── translate.py          # Kiswahili → English translation
│   ├── azure_tts.py          # Azure Neural TTS
│   ├── tts.py                # gTTS fallback
│   ├── export_excel.py       # Excel export logic
│   ├── state.py              # In-memory runtime state
│   ├── logger.py             # Logging configuration
│   └── utils.py              # Shared utilities
├── data/                     # Participant data and recordings (gitignored)
├── config.yaml               # Survey questions and configuration
├── main.py                   # App entry point
├── run_app.py                # One-command local launcher (ngrok + Flask)
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=your_azure_region
SECRET_KEY=your_flask_secret
```

### 3. Run locally

```bash
python3 run_app.py
```

This will:
- Start or reuse an ngrok tunnel on port `5050`
- Set `PUBLIC_BASE_URL` automatically
- Launch the Flask app
- Open the admin dashboard in your browser

---

## Configuration

Survey questions and call settings are managed in `config.yaml`:

```yaml
survey_questions:
  - id: q1
    text: "..."
  - id: q2
    text: "..."
```

---

## Data & Privacy

- All participant phone numbers and recordings are stored locally and are **gitignored**
- PII is never committed to version control
- Passwords are hashed using PBKDF2 (scrypt)
- JWT tokens are used for dashboard session management

---

## Documentation

Full technical documentation is available in [`DOCUMENTATION.md`](DOCUMENTATION.md) / [`DOCUMENTATION.pdf`](DOCUMENTATION.pdf), covering:

- System architecture
- API reference (all Twilio webhook endpoints)
- ML pipeline design
- Data models and Excel export format
- Admin dashboard usage
- Deployment guide
- Security model

---

## Author

**Krishnanand**  
AudioSurvey AI Research Platform · v1.2.0 · April 2026
