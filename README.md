# AudioSurvey AI
🚧 Status: Under Development

AI-powered multilingual IVR voice survey system using Twilio, Speech-to-Text, Translation, and Text-to-Speech.

## Current Features
- Outbound and inbound IVR calls
- Multi-question voice survey flow
- Full-call audio recording
- Speech transcription
- Language detection & English translation
- English audio generation (TTS)

## Tech Stack
- Python (Flask)
- Twilio Voice API
- Whisper (Speech-to-Text)
- Hugging Face / Translation
- Mozilla / Coqui TTS
- ngrok

## Quick Local Start
Run one command:

```bash
python3 run_app.py
```

What it does:
- Starts or reuses an ngrok tunnel on port `5050`
- Sets `PUBLIC_BASE_URL` automatically
- Starts `python3 -m app.twilio_handler serve`
- Opens the public URL in your browser

## Status
This project is actively under development.
