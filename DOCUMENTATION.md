---
title: " "
pdf_options:
  displayHeaderFooter: false
  margin:
    top: 15mm
    bottom: 15mm
    left: 15mm
    right: 15mm
  printBackground: true
---

<style>
  h1, h2, h3, h4 { page-break-after: avoid; }
  tr { page-break-inside: avoid; }
</style>

<p align="center">
  <strong>AudioSurvey AI</strong><br/>
  <em>AI-Powered Multilingual IVR Voice Survey Platform</em>
</p>

<p align="center">
  <code>Version 1.1.0</code> &nbsp;|&nbsp; <code>Last Updated: 2026-03-20</code> &nbsp;|&nbsp; <code>Classification: Internal</code>
</p>

---

# Project Documentation

## Revision History

| Version | Date | Author | Change Description |
|---------|------|--------|--------------------|
| 1.0.0 | 2026-02-22 | Krishnanand | Initial release — core IVR engine, Twilio integration, Whisper STT, admin dashboard |
| 1.0.1 | 2026-02-26 | Krishnanand | Excel export support for survey responses |
| 1.0.2 | 2026-03-01 | Krishnanand | Excel formatting corrections, UX/UI upgrade, audio channel fix for full-call recordings |
| 1.0.3 | 2026-03-03 | Krishnanand | Updated survey questions, system cleanup |
| 1.0.4 | 2026-03-04 | Krishnanand | English translation export, "Convert to English" button added |
| 1.0.5 | 2026-03-05 | Krishnanand | Authentication system — login/logout, brute-force protection, session management |
| 1.0.6 | 2026-03-05 | Krishnanand | Full call testing, results saved and verified end-to-end |
| 1.0.7 | 2026-03-08 | Krishnanand | MCQO digit bug fix, hardcoded button logic corrected |
| 1.0.8 | 2026-03-10 | Krishnanand | DeepFilterNet background noise removal, random crash fix, log improvements |
| 1.0.9 | 2026-03-15 | Krishnanand | macOS DMG packaging, icon generator update |
| 1.1.0 | 2026-03-17 | Krishnanand | File naming convention refactored, auth info cleanup, documentation |

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Executive Summary](#1-executive-summary) | High-level project overview and objectives |
| 2 | [System Architecture](#2-system-architecture) | Architecture diagrams, component topology, tech stack |
| 3 | [Component Design](#3-component-design) | Deep dive into each module and its responsibilities |
| 4 | [Data Flow & Pipelines](#4-data-flow--pipelines) | End-to-end data lifecycle and ML processing pipeline |
| 5 | [API Reference](#5-api-reference) | Complete HTTP endpoint documentation |
| 6 | [Data Models & State Schema](#6-data-models--state-schema) | JSON schemas, state machine, data persistence |
| 7 | [Authentication & Security](#7-authentication--security) | Auth flow, brute-force protection, session management |
| 8 | [Survey Question Engine](#8-survey-question-engine) | Question format specification and IVR call flow |
| 9 | [Configuration Reference](#9-configuration-reference) | All configuration files and environment variables |
| 10 | [Admin Dashboard](#10-admin-dashboard) | UI features, live polling, user workflows |
| 11 | [Background Services](#11-background-services) | Scheduler, ML worker, and concurrency model |
| 12 | [Error Handling & Resilience](#12-error-handling--resilience) | Fault tolerance, retry logic, graceful degradation |
| 13 | [Logging & Observability](#13-logging--observability) | Logging architecture, audit trails, monitoring |
| 14 | [Deployment Guide](#14-deployment-guide) | Local setup, ngrok tunneling, macOS DMG packaging |
| 15 | [Directory Structure](#15-directory-structure) | Complete project tree with annotations |
| 16 | [Dependency Matrix](#16-dependency-matrix) | Third-party libraries and their roles |
| 17 | [Glossary](#17-glossary) | Domain terminology and abbreviations |

---

## 1. Executive Summary

### 1.1 Purpose

AudioSurvey AI is an AI-powered multilingual Interactive Voice Response (IVR) survey platform designed to conduct automated voice-based research surveys over telephone calls. The system targets **African refugees who speak Kiswahili**, enabling researchers to collect structured survey responses at scale without requiring in-person enumerators.

### 1.2 Business Context

The platform was built for academic and public health research. It is designed as a **flexible, multi-survey system** — the survey topic, questions, and thematic sections are fully configurable via the `data/questions.txt` file. Researchers can deploy different surveys for different studies without any code changes.

### 1.3 Key Capabilities

| Capability | Description |
|------------|-------------|
| **Automated Outbound Calling** | Scheduled batch dialing of research participants via Twilio |
| **Inbound Call Support** | Participants can call in and complete the survey |
| **Multilingual IVR** | Survey prompts spoken in Kiswahili via Azure Neural TTS |
| **Multi-Format Questions** | INFO, OPEN (speech), MCQ (DTMF keypad), MCQO (MCQ + "Other" speech) |
| **Full-Call Recording** | Complete audio capture of every call (up to 30 minutes) |
| **AI Audio Processing** | Background noise removal via DeepFilterNet |
| **Speech-to-Text** | Post-call transcription using OpenAI Whisper (large-v3) |
| **Machine Translation** | Automatic Kiswahili to English translation |
| **English Audio Generation** | TTS synthesis of translated responses |
| **Structured Data Export** | Excel export of MCQ/MCQO responses (original + English) |
| **Admin Dashboard** | Real-time web UI for managing participants, scheduling, and monitoring |
| **Conference Calling** | Three-way call support for researcher-moderated interviews |
| **macOS Distribution** | Packaged as a native .app inside a DMG installer |

### 1.4 Technology Summary

| Layer | Technology |
|-------|-----------|
| **Runtime** | Python 3.x |
| **Web Framework** | Flask 3.1.2 |
| **Telephony** | Twilio Voice API |
| **Live Speech Recognition** | Twilio `<Gather>` (Kiswahili `sw-KE`) |
| **Post-Call Transcription** | OpenAI Whisper `large-v3` |
| **Text-to-Speech (Prompts)** | Azure Cognitive Services (Neural SSML) |
| **Text-to-Speech (Output)** | Google TTS (gTTS) |
| **Translation** | Google Translate (googletrans) |
| **Noise Reduction** | DeepFilterNet (PyTorch-based) |
| **Audio Processing** | FFmpeg, pydub |
| **Data Export** | pandas + openpyxl |
| **Tunneling** | ngrok |
| **Packaging** | macOS .app bundle + DMG |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
+-----------------------------------------------------------------------+
|                         EXTERNAL SERVICES                             |
|   +------------------+  +------------------+  +------------------+    |
|   | Twilio Voice API |  | Azure Cognitive  |  | Google Translate |    |
|   |                  |  | Services (TTS)   |  |                  |    |
|   +--------+---------+  +--------+---------+  +--------+---------+    |
|            |                     |                      |             |
+-----------------------------------------------------------------------+
             |                     |                      |
             v                     v                      v
+-----------------------------------------------------------------------+
|                    FLASK APPLICATION SERVER (:5050)                    |
|                                                                       |
|   +--------------+  +--------------+  +--------------+                |
|   | Auth Module  |  | IVR Webhook  |  |    Admin     |                |
|   |              |  | Handlers     |  |  Dashboard   |                |
|   +--------------+  +--------------+  +--------------+                |
|                                                                       |
|   +--------------+  +--------------+  +--------------+                |
|   | Conference   |  | Excel Export |  | ngrok Tunnel |                |
|   | Call Module  |  |              |  | Integration  |                |
|   +--------------+  +--------------+  +--------------+                |
|                                                                       |
|   +-----------------------------+                                     |
|   |     BACKGROUND SERVICES     |                                     |
|   |  +----------+ +-----------+ |                                     |
|   |  | Scheduler| | ML Worker | |                                     |
|   |  | (15s)    | | (5s poll) | |                                     |
|   |  +----------+ +-----------+ |                                     |
|   +-----------------------------+                                     |
+-----------------------------------------------------------------------+
             |                     |
             v                     v
+-----------------------------------------------------------------------+
|                      ML PROCESSING PIPELINE                           |
|   +--------------+  +-----------+  +------------+  +-----------+      |
|   | DeepFilterNet|->| Whisper   |->| Translation|->| English   |      |
|   | (Denoise)    |  | large-v3  |  | (sw -> en) |  | TTS       |      |
|   +--------------+  +-----------+  +------------+  +-----------+      |
+-----------------------------------------------------------------------+
             |
             v
+-----------------------------------------------------------------------+
|                       LOCAL FILE STORAGE                              |
|                                                                       |
|   data/state/          data/audio/           data/audio_processed/    |
|   data/transcripts/    data/translations/    data/english_audio/      |
|   data/results/        data/ivr_audio/                                |
+-----------------------------------------------------------------------+
```

**Data flow summary:**

- Participant Phone <--> Twilio <--> ngrok <--> IVR Webhook Handlers
- Admin Browser --> ngrok --> Auth Module --> Dashboard
- IVR Handlers --> Azure TTS --> data/ivr_audio/
- IVR Handlers --> Recording Done --> ML Worker
- ML Worker --> DeepFilterNet --> Whisper --> Translation --> English TTS
- Translation --> Google Translate API
- Scheduler --> Twilio (dial eligible participants)
- Excel Export --> data/state/ --> data/results/

### 2.2 Network Topology

```
+------------------------------------------------------------------+
|                          INTERNET                                |
|                                                                  |
|   +------------------+           +------------------+            |
|   | Participant      |           | Admin Browser    |            |
|   | (Kiswahili       |           |                  |            |
|   |  Speaker)        |           +--------+---------+            |
|   +--------+---------+                    |                      |
|            |                              |                      |
|            | PSTN/VoIP                    | HTTPS                |
|            v                              v                      |
|   +------------------+                                           |
|   | Twilio Cloud     |                                           |
|   | (Voice Infra)    |                                           |
|   +--------+---------+                                           |
|            |                                                     |
+------------------------------------------------------------------+
             | HTTPS Webhooks
             v
+------------------------------------------------------------------+
|                    LOCAL MACHINE (macOS)                          |
|                                                                  |
|   +------------------+         +------------------+              |
|   | ngrok Process    | <-----> | Flask Server     |              |
|   | :4040 (API)      | local   | :5050            |              |
|   +------------------+ host    +--------+---------+              |
|                                         |                        |
|                                         | REST API               |
|                                         v                        |
|                                +------------------+              |
|                                | Azure TTS        |              |
|                                | (East US Region) |              |
|                                +------------------+              |
+------------------------------------------------------------------+
```

### 2.3 Thread Architecture

```
+------------------------------------------------------------------+
|                    PYTHON MAIN PROCESS                            |
|                                                                  |
|   +-------------------+                                          |
|   | Main Thread       |---> start_background_services()          |
|   | (Flask WSGI)      |          |            |                  |
|   +-------------------+          |            |                  |
|                                  v            v                  |
|   +-------------------+   +-------------------+                  |
|   | Scheduler Thread  |   | Worker Thread     |                  |
|   | (daemon, 15s loop)|   | (daemon, 5s poll) |                  |
|   +-------------------+   +-------------------+                  |
|            |                       |                             |
|            +----------+------------+                             |
|                       |                                          |
|                       v                                          |
|              +-----------------+                                 |
|              | threading.RLock |                                  |
|              | (STATE_IO_LOCK) |                                  |
|              +--------+--------+                                 |
|                       |                                          |
|                       v                                          |
|              +-----------------+                                 |
|              | participants.json                                 |
|              | call_log.csv                                      |
|              | settings.json   |                                 |
|              +-----------------+                                 |
+------------------------------------------------------------------+
```

---

## 3. Component Design

### 3.1 Module Dependency Graph

```
  run_app.py ---------(subprocess)---------> twilio_handler.py
  (Launcher)                                  (Flask App + IVR)
                                                     |
            +----------+----------+---------+--------+--------+------+
            |          |          |         |        |        |      |
            v          v          v         v        v        v      v
       dashboard.py  scheduler.py  state.py  utils.py  export_excel.py
       (Admin UI)    (Call Sched.) (State)   (Helpers) (Excel Export)
            |          |                                       |
            v          v                                       v
         state.py   state.py                              translate.py

  twilio_handler.py ---+----------+-----------+
                       |          |           |
                       v          v           v
              background_worker.py  transcribe.py  file_naming.py
              (ML Pipeline)         (Whisper STT)  (Safe Names)
                       |
          +------------+----------+-----------+
          |            |          |           |
          v            v          v           v
  audio_preprocess.py  transcribe.py  translate.py  tts.py
  (DeepFilterNet)      (Whisper)      (Translation) (Google TTS)

  main.py -------> transcribe.py, translate.py, tts.py
  (Batch Pipeline)

  Supporting:  logger.py (Colored Logging)
               auth.py (Authentication)
               azure_tts.py (Azure TTS)
               runtime_warnings.py (Warning Suppression)
               twilio_utils.py (Twilio Call Helpers)
```

### 3.2 Module Descriptions

| Module | Lines | Responsibility |
|--------|-------|---------------|
| `twilio_handler.py` | ~1,330 | Core Flask application. Defines all IVR webhook routes, Azure TTS for call prompts, auth login/logout flows, conference calling, recording download, and application bootstrap. Acts as the central orchestrator. |
| `dashboard.py` | ~950 | Admin web dashboard. Renders the single-page HTML UI with inline CSS/JS. Handles participant management routes (upload, schedule, pause/resume, reset, dial now). Includes live-polling JSON endpoint. |
| `state.py` | ~240 | Thread-safe participant state management. Handles JSON persistence with atomic writes, call eligibility logic (`can_call`), state transitions, retry gap enforcement, and participant schema migration. |
| `export_excel.py` | ~310 | Builds structured Excel exports from participant responses. Decodes DTMF digits back to option text, filters out OPEN responses, supports both original-language and English-translated exports. |
| `background_worker.py` | ~150 | Continuous polling worker that processes completed recordings through the 4-stage ML pipeline (denoise, transcribe, translate, TTS). Shows terminal progress bars. |
| `scheduler.py` | ~115 | Timed call dispatcher. Runs every 15 seconds, checks participant eligibility, and places Twilio calls for scheduled participants. Supports force-dial mode. |
| `audio_preprocess.py` | ~210 | Audio noise removal pipeline using DeepFilterNet. Handles FFmpeg-based channel extraction/resampling, PyTorch-based noise removal, and output resampling for Whisper. |
| `transcribe.py` | ~50 | Whisper large-v3 speech-to-text. Transcribes audio files with Swahili language hint, returns text and detected language. Supports both single-file and directory batch modes. |
| `translate.py` | ~135 | Chunked Google Translate integration. Splits long texts at sentence boundaries, retries failed chunks, marks failures with placeholder tags. |
| `tts.py` | ~55 | Google TTS (gTTS) wrapper for generating English MP3 audio from translated text. Skips files with translation failure markers. |
| `auth.py` | ~165 | Standalone authentication module (partially duplicated in `twilio_handler.py`). Provides brute-force protection, session management, and credential verification. |
| `utils.py` | ~25 | Scheduling utility. Converts NYC local time to UTC and updates participant state. |
| `azure_tts.py` | ~50 | Standalone Azure TTS module with disk caching. Used for generating call prompt audio. |
| `file_naming.py` | ~28 | Safe filename generation. Sanitizes participant IDs and generates timestamped base names. |
| `logger.py` | ~75 | Colored console logging via `colorlog`. Silences noisy third-party library logs. Provides context manager for extra-quiet operations. |
| `runtime_warnings.py` | ~15 | Suppresses urllib3 OpenSSL compatibility warnings. |
| `run_app.py` | ~130 | Application launcher. Auto-starts ngrok, sets environment variables, launches Flask, opens browser. |
| `main.py` | ~28 | Standalone batch processor for offline audio to transcript to translation to TTS pipeline. |

---

## 4. Data Flow & Pipelines

### 4.1 Outbound Call Lifecycle

```
  ADMIN                DASHBOARD          SCHEDULER          TWILIO
    |                      |                  |                 |
    |-- Upload CSV ------->|                  |                 |
    |                      |-- upsert_participant()            |
    |                      |                  |                 |
    |-- Set schedule ----->|                  |                 |
    |                      |-- schedule_participant()          |
    |                      |                  |                 |
    |-- Click "Start" ---->|                  |                 |
    |                      |-- set_paused(false)               |
    |                      |                  |                 |
    |                      |    +--[Every 15 seconds]--+       |
    |                      |    | load_participants()  |       |
    |                      |    | can_call() check     |       |
    |                      |    |    Checks: status,   |       |
    |                      |    |    attempts, schedule |       |
    |                      |    |    time, retry gap   |       |
    |                      |    +----------------------+       |
    |                      |                  |                 |
    |                      |                  |-- calls.create --->
    |                      |                  |-- mark_call_started()
    |                      |                  |                 |

  TWILIO             PARTICIPANT          IVR HANDLER       AZURE TTS
    |                      |                  |                 |
    |-- Ring ------------->|                  |                 |
    |<-- Answer -----------|                  |                 |
    |-- POST /voice --------------------->|                    |
    |                      |              | Start recording    |
    |                      |              |-- Redirect /start  |
    |-- POST /start --------------------->|                    |
    |                      |              |-- Generate TTS --->|
    |                      |              |<-- MP3 audio ------|
    |<-- TwiML: Play intro + Gather ------|                    |
    |                      |                  |                 |
    |    +--[For each question]--+            |                 |
    |    | Speech / DTMF input   |            |                 |
    |    | POST /next?q=N        |            |                 |
    |    | Store response        |            |                 |
    |    | Generate TTS          |            |                 |
    |    | Play question + Gather|            |                 |
    |    +-----------------------+            |                 |
    |                      |                  |                 |
    |<-- Play "Kwaheri" + Hangup ------------|                 |
    |-- POST /call-status (completed) ------>|                 |
    |                      |              | mark_call_result() |
    |                      |              | append_to_excel()  |
    |-- POST /recording-done --------------->|                 |
    |                      |              | Download WAV       |
    |                      |              | processing = pending
```

### 4.2 ML Processing Pipeline

```
 INPUT                STAGE 1                STAGE 2          STAGE 3              STAGE 4      OUTPUTS
                   Audio Preprocessing     Transcription     Translation         English TTS

+-----------+     +---------------+     +-----------+     +-------------+     +---------+     +-----------+
| Raw       |     | FFmpeg        |     |           |     | Language    |     |         |     | Cleaned   |
| Recording |---->| Channel       |     |           |     | Detection   |     |         |     | WAV       |
| (Stereo   |     | Extract +     |     |           |     |     |       |     |         |     +-----------+
|  WAV)     |     | Resample 48kHz|     |           |     |  +--+--+   |     |         |     | Transcript|
+-----------+     +-------+-------+     |           |     |  |     |   |     |         |     | .txt      |
                          |             |           |     |  v     v   |     |         |     +-----------+
                  +-------+-------+     |           |     |lang  lang  |     |         |     | Translation
                  | DeepFilterNet |     |           |     |=en   !=en  |     |         |     | .txt      |
                  | Noise Removal |     |           |     | |     |    |     |         |     +-----------+
                  | (PyTorch)     |     |           |     | |   Chunk  |     |         |     | English   |
                  +-------+-------+     | Whisper   |     |Copy Splitter|    |         |     | .mp3      |
                          |             | large-v3  |     |as-is (3000) |    |         |     +-----------+
                  +-------+-------+     | lang='sw' |     | |     |    |     |         |
                  | FFmpeg        |     | temp=0.0  |     | | Google   |     | gTTS    |
                  | Resample 16kHz|---->|           |---->| |Translate |---->| lang=en |
                  | Mono PCM     |     |           |     | | sw->en   |     |         |
                  +---------------+     +-----------+     | |(3 retries|     +---------+
                                                          | |  Join   |
                                                          +--+-------+
```

### 4.3 Recording Callback Flow

```
  Twilio POST /recording-done
       |
       v
  Recording completed?
       |           |
      No          Yes
       |           |
  Return 200    Recording URL present?
                   |           |
                  No          Yes
                   |           |
              Return 400    Find participant by CallSid
                               |
                        Known participant?
                           |           |
                          No          Yes
                           |           |
                   Download WAV    Call status retryable failure?
                   anyway          (no-answer/busy/failed/canceled)
                                       |           |
                                      Yes         No
                                       |           |
                                  Skip pipeline  Participant engaged?
                                                   |           |
                                                  No          Yes
                                                   |           |
                                             Skip pipeline   Download WAV from Twilio
                                             (no speech)         |
                                                            Save to data/audio/
                                                                 |
                                                            Set processing_status = pending
                                                                 |
                                                            Log call event to CSV
                                                                 |
                                                            Background Worker
                                                            picks up next cycle
```

### 4.4 Excel Export Data Flow

```
  INPUT                         PROCESSING                         OUTPUT

  +---------------+     +---------------------+     +---------------------------+
  | questions.txt |---->| Build Response      |     | ivr_responses.xlsx        |
  +---------------+     | Metadata            |     | (Kiswahili)               |
                        +----------+----------+     +-------------+-------------+
  +-----------------+              |                               |
  | participants.json|-->| Filter Responses   |     Cell-by-cell translate
  +-----------------+   | (exclude OPEN)      |                    |
                        +----------+----------+     +-------------+-------------+
                                   |                | Translation Cache         |
                        +----------+----------+     +-------------+-------------+
                        | Decode DTMF         |                    |
                        | -> Option Text      |     +-------------+-------------+
                        +----------+----------+     | ivr_responses_english.xlsx|
                                   |                | (English)                 |
                        +----------+----------+     +---------------------------+
                        | Renumber Question   |
                        | Keys                |
                        +----------+----------+
                                   |
                        +----------+----------+
                        | Build DataFrame     |-------> ivr_responses.xlsx
                        +---------------------+
```

---

## 5. API Reference

### 5.1 Public Endpoints (No Auth Required)

These endpoints are accessible without authentication — they are called by Twilio webhooks or used for health checks.

#### `POST /voice`
> **Twilio Inbound Call Entrypoint**

Initiates full-call recording and redirects to the survey start.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `CallSid` | Twilio | Unique call identifier |
| `From` | Twilio | Caller phone number |

**Response:** TwiML — starts `<Recording>`, redirects to `/start`

---

#### `POST /start`
> **Survey Introduction**

Plays the first 2 intro prompts (INFO questions), then begins the first survey question.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `CallSid` | Twilio | Call identifier |

**Response:** TwiML — plays intros, gathers first OPEN question

---

#### `POST /next?q={index}`
> **Survey Question Router**

Core question loop. Stores previous answer, advances to next question based on type.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `q` | Query string | 0-based question index |
| `CallSid` | Twilio | Call identifier |
| `SpeechResult` | Twilio | Transcribed speech (OPEN questions) |

**Response:** TwiML — varies by question type (Gather speech / Gather DTMF / Play + Redirect)

---

#### `POST /mcq-handler?q={index}`
> **MCQ/MCQO DTMF Handler**

Processes keypad digit for multiple choice questions. If MCQO and "Other" selected, redirects to speech capture.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `q` | Query string | Question index |
| `Digits` | Twilio | Pressed DTMF digit (1-9) |
| `CallSid` | Twilio | Call identifier |

**Response:** TwiML — either redirects to next question or to `/mcqo-other-handler`

---

#### `POST /mcqo-other-handler?q={index}`
> **MCQO "Other" Speech Handler**

Captures (but does not store) the free-speech "Other" response and moves to the next question.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `q` | Query string | Question index |
| `SpeechResult` | Twilio | Free-speech "Other" response |

**Response:** TwiML — redirects to `/next?q={q+1}`

---

#### `POST /call-status`
> **Twilio Call Status Webhook**

Receives call completion events. Updates participant state and triggers Excel export on completion.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `CallSid` | Twilio | Call identifier |
| `CallStatus` | Twilio | One of: `completed`, `no-answer`, `busy`, `failed`, `canceled` |

**Response:** `200 OK`

---

#### `POST /recording-done`
> **Twilio Recording Completion Webhook**

Downloads the completed recording WAV and queues it for ML processing.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `CallSid` | Twilio | Call identifier |
| `RecordingUrl` | Twilio | URL to download recording |
| `RecordingStatus` | Twilio | `completed` or other |

**Response:** `200 OK`

---

#### `GET /health`
> **Health Check**

Simple liveness probe.

**Response:** `200 OK` — body: `ok`

---

#### `POST /conference_host`, `POST /conference_join`, `POST /conference_ivr`, `POST /conference_ivr_next`
> **Conference Call Endpoints**

Handle the Twilio conference call flow. The host enters a waiting room where IVR questions play, then the conference starts when all questions are complete.

---

#### `POST /silence`
> **Silence Generator**

Returns TwiML with a 60-second pause. Used as conference hold music fallback.

---

#### `GET /ivr-audio/<filename>`
> **Static IVR Audio Server**

Serves pre-generated Azure TTS audio files from `data/ivr_audio/`.

---

### 5.2 Authenticated Endpoints (Login Required)

All `/admin/*` routes require an active session (cookie-based) or a valid `ADMIN_TOKEN` query parameter.

#### `GET /admin`
> **Admin Dashboard**

Renders the full admin dashboard HTML page.

**Response:** `200 OK` — HTML page

---

#### `GET /admin/live_state`
> **Live State JSON API**

Returns current participant state for live-polling dashboard updates.

**Response:**
```json
{
  "total": 42,
  "counts": {
    "pending": 10,
    "in_progress": 5,
    "completed": 25,
    "failed": 2
  },
  "participants": [
    {
      "participant_id": "P001",
      "phone_masked": "+2******1234",
      "status": "completed",
      "attempts": 1,
      "engaged": true,
      "scheduled_local": "2026-03-15 14:00",
      "scheduled_input": "2026-03-15 14:00"
    }
  ]
}
```

---

#### `POST /admin/upload_contacts`
> **Upload Participant CSV**

Accepts a CSV file with headers `participant_id,phone_e164`. Creates participant entries with `idle` status (not immediately callable).

---

#### `POST /admin/save_questions`
> **Save Survey Questions**

Saves the survey question text to `data/questions.txt`.

---

#### `POST /admin/schedule`
> **Schedule Participant Call**

Sets a participant's scheduled call time (NYC timezone).

| Parameter | Source | Description |
|-----------|--------|-------------|
| `participant_id` | Form | Participant ID |
| `local_time` | Form | `YYYY-MM-DD HH:MM` (NYC time) |

---

#### `POST /admin/dial_now`
> **Force Dial**

Triggers `run_once(force=True)` — calls all eligible participants immediately, bypassing schedule/retry timing.

---

#### `POST /admin/pause` / `POST /admin/resume`
> **System Pause / Resume**

Toggles the global scheduler pause state.

---

#### `POST /admin/reset_state`
> **Reset State**

Creates timestamped backups of `participants.json` and `call_log.csv`, then resets all state.

---

#### `GET /admin/export_excel`
> **Export Survey Responses (Original Language)**

Downloads `ivr_responses.xlsx` containing MCQ/MCQO responses with option text decoded.

---

#### `GET /admin/export_excel_english`
> **Export Survey Responses (English)**

Translates all response cells to English and downloads `ivr_responses_english.xlsx`.

---

#### `POST /admin/conference_call`
> **Start Conference Call**

Dials two phone numbers into a shared Twilio conference room.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `number_1` | Form | First phone number (E.164) |
| `number_2` | Form | Second phone number (E.164) |

---

### 5.3 Authentication Endpoints

#### `GET /login`
> **Login Page**

Renders the login form.

---

#### `POST /login`
> **Login Submit**

Authenticates the user against `config.yaml` password hashes.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `username` | Form | Username (case-insensitive) |
| `password` | Form | Plaintext password |

**Responses:**
- Success: redirect to `/admin`
- Invalid credentials: re-render login page with error
- Locked out: show remaining lockout time

---

#### `POST /logout`
> **Logout**

Clears the session and logs the event.

---

## 6. Data Models & State Schema

### 6.1 Participant Schema

Each participant in `data/state/participants.json` follows this schema:

```json
{
  "P001": {
    "status": "pending",
    "attempts": 0,
    "last_call_time": null,
    "last_call_sid": null,
    "last_call_status": null,
    "engaged": false,
    "last_recording_url": null,
    "last_outputs": {},
    "scheduled_time_local": null,
    "scheduled_time_utc": null,
    "phone_e164": "+254700000000",
    "responses": {
      "q1": "2",
      "q2": "1",
      "q3": "3"
    },
    "survey_q_counter": 3,
    "processing_status": "completed",
    "audio_path": "data/audio/P001_20260315_140000.wav",
    "recording_url": "https://api.twilio.com/2010-04-01/Accounts/.../Recordings/RE..."
  }
}
```

### 6.2 Participant State Machine

```
                          +-------+
                          | START |
                          +---+---+
                              |
                          CSV upload
                              |
                              v
                          +-------+
                   +----->| idle  |
                   |      +---+---+
                   |          |
                   |     Schedule set
                   |          |
                   |          v
                   |    +---------+       Eligible for calling when:
                   +----|         |       - scheduled_time_utc <= now
                   |    | pending |       - retry gap (1h) elapsed
                   |    |         |       - attempts < 3
                   |    +----+----+
                   |         |
                   |    Call placed
                   |         |
                   |         v
                   |  +-------------+
                   |  | in_progress |
                   |  +------+------+
                   |         |
              +----+---------+---------+-------------------+
              |              |                             |
        No answer /    Survey finished              Completed but
        Busy           (engaged=true)               not engaged
        (attempts<3)         |                             |
              |              v                             |
              |      +-----------+                         |
              +      | completed |                         |
                     +-----------+                         |
                                                           |
              +--------------------------------------------+
              |
        No answer / Busy
        (attempts >= 3)
              |
              v
         +--------+
         | failed |
         +--------+
```

### 6.3 Processing Status State Machine

```
  +-------+     No recording     +------+
  | START |--------------------->| none |
  +-------+                      +--+---+
                                    |
                           Recording downloaded
                                    |
                                    v
                                +---------+
                                | pending |
                                +----+----+
                                     |
                               Worker picks up
                                     |
                                     v
                               +------------+
                               | processing |
                               +-----+------+
                                     |
                         +-----------+-----------+
                         |                       |
                   Pipeline success        Pipeline error
                         |                       |
                         v                       v
                   +-----------+           +--------+
                   | completed |           | failed |
                   +-----------+           +--------+
```

### 6.4 Call Log Schema

`data/state/call_log.csv` columns:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp_utc` | ISO 8601 | Event timestamp |
| `participant_id` | String | Participant identifier |
| `phone_masked` | String | Masked phone (e.g., `+2******1234`) |
| `direction` | String | `inbound` or `outbound-api` |
| `call_sid` | String | Twilio call SID |
| `recording_url` | URL | Twilio recording URL |
| `audio_path` | String | Local file path |
| `transcript_path` | String | Local transcript path |
| `translation_path` | String | Local translation path |
| `english_audio_path` | String | Local English audio path |

### 6.5 Auth State Schema

`data/auth_state.json`:
```json
{
  "fails": {
    "username|ip_address": [1711234567, 1711234580]
  },
  "locks": {
    "username|ip_address": 1711235467
  }
}
```

### 6.6 Settings Schema

`data/state/settings.json`:
```json
{
  "paused": false
}
```

---

## 7. Authentication & Security

### 7.1 Authentication Flow

```
  USER                    FLASK               config.yaml       auth_state.json    auth_log.jsonl
   |                        |                      |                  |                 |
   |-- GET /admin --------->|                      |                  |                 |
   |                        |-- before_request     |                  |                 |
   |<-- 302 -> /login ------|   guard              |                  |                 |
   |                        |                      |                  |                 |
   |-- POST /login -------->|                      |                  |                 |
   |   (username, password) |                      |                  |                 |
   |                        |-- is_locked? ------->|                  |                 |
   |                        |                      |                  |                 |
   |              +---------+--- [If Locked] ------+------------------+                 |
   |              |         |                      |                  |                 |
   |<-- "Too many attempts" |                      |                  |                 |
   |                        |                      |                  |                 |
   |                        |-- Load auth.users -->|                  |                 |
   |                        |-- check_password_hash()                 |                 |
   |                        |                      |                  |                 |
   |              +---------+-- [If Invalid] ------+------------------+                 |
   |              |         |-- record_fail ------>|                  |                 |
   |              |         |   (If fails>=7 in 10min -> lock 15min) |                 |
   |              |         |-- Log failed ------->|                  |--- append ----->|
   |<-- "Invalid credentials"                      |                  |                 |
   |                        |                      |                  |                 |
   |              +---------+-- [If Valid] --------+------------------+                 |
   |              |         |-- clear_fails ------>|                  |                 |
   |              |         |-- Set session cookie |                  |                 |
   |              |         |-- Log success ------>|                  |--- append ----->|
   |<-- 302 -> /admin ------|                      |                  |                 |
```

### 7.2 Security Measures

| Measure | Implementation | Details |
|---------|---------------|---------|
| **Password Hashing** | PBKDF2-SHA256 | 1,000,000 iterations via Werkzeug |
| **Brute-Force Protection** | Rate limiting | 7 failures in 10 minutes -> 15-minute lockout per username+IP |
| **Session Security** | Flask sessions | `HttpOnly`, `SameSite=Lax`, `Secure=True`, 8-hour lifetime |
| **Phone Masking** | `mask_phone()` | Only first 2 + last 4 digits shown (e.g., `+2******1234`) |
| **PII Protection** | `.gitignore` | Contacts CSV, participant state, audio, and logs are git-ignored |
| **Route Protection** | `@app.before_request` | All `/admin` routes require session or admin token |
| **Webhook Passthrough** | Allowlist | Twilio webhook paths (`/voice`, `/next`, etc.) bypass auth |
| **Audit Logging** | JSONL | Every login/logout event logged with IP, user-agent, timestamps |

### 7.3 Request Guard Logic

```
  Incoming Request
       |
       v
  Path starts with allowed prefix?
       |
       +-- /login, /health, /voice, /start, /next,
       |   /call-status, /recording-done, /ivr-audio/, etc.
       |       |
       |       +---> [ALLOW] Pass through
       |
       +-- /admin/*
       |       |
       |       v
       |   ADMIN_TOKEN set & matches?
       |       |          |
       |      Yes        No
       |       |          |
       |   [ALLOW]    Session has 'user' key?
       |                  |          |
       |                 Yes        No
       |                  |          |
       |              [ALLOW]    [REDIRECT -> /login]
       |
       +-- Other paths
               |
               +---> [ALLOW] No guard
```

---

## 8. Survey Question Engine

### 8.1 Question File Format

Questions are stored in `data/questions.txt` using a pipe-delimited format:

```
TYPE|Question Text|Option1|Option2|...
```

### 8.2 Supported Question Types

| Type | Format | Input Method | Response Storage | Example |
|------|--------|-------------|-----------------|---------|
| **INFO** | `INFO\|text` | None (read-only) | Not stored | `INFO\|Maswali sehemu ya kwanza` |
| **OPEN** | `OPEN\|text` | Speech (`<Gather input="speech">`) | Raw speech text | `OPEN\|Tafadhali sema jina lako` |
| **MCQ** | `MCQ\|text\|opt1\|opt2\|opt3` | DTMF keypad (`<Gather input="dtmf">`) | Digit (1-9) | `MCQ\|Nani..?\|Marafiki\|Mume\|Watoto` |
| **MCQO** | `MCQO\|text\|opt1\|opt2\|Nyingine` | DTMF + optional speech | Digit (1-9) | `MCQO\|Kupanga..?\|Ndiyo\|Hapana\|Nyingine` |

### 8.3 IVR Question Flow

```
  Call Answered
       |
       v
  Start Full-Call Recording (30 min max)
       |
       v
  Play Q[0] + Q[1] (INFO intros)
       |
       v
  Play Q[2] (First real question)
       |
       v
  +--- Question Type? ---+------------------+------------------+
  |                       |                  |                  |
  INFO                   OPEN               MCQ               MCQO
  |                       |                  |                  |
  Play text              Play text          Play text          Play text
  |                      Gather speech      + options          + options
  |                      timeout=6s         Gather 1 digit     Gather 1 digit
  |                       |                  |                  |
  |                      Store              Store              Digit == Other?
  |                      SpeechResult       Digit               |        |
  |                       |                  |                 No       Yes
  |                       |                  |                  |        |
  |                       |                  |              Store    "Umechagua
  |                       |                  |              Digit   nyingine..."
  |                       |                  |                  |   Gather speech
  |                       |                  |                  |        |
  +---+-------------------+------------------+--------+---------+--------+
      |
      v
  Advance to Q[n+1]
      |
      v
  More questions?
      |         |
     Yes       No
      |         |
  [loop]    Play "Kwaheri" + Hangup
```

### 8.4 TTS Prompt Generation

Survey prompts are spoken aloud using **Azure Cognitive Services Neural TTS**:

- **Voice:** `sw-KE-ZuriNeural` (Swahili) / `en-US-JennyNeural` (English)
- **Rate:** `-15%` prosody for clearer, slower speech
- **Caching:** SHA1 hash of `voice|format|text` to disk-cached MP3 in `data/ivr_audio/`
- **Serving:** Public URL via `/ivr-audio/{hash}.mp3`, referenced in TwiML `<Play>` tags
- **Format:** SSML with XML entity escaping

### 8.5 MCQ Option Verbalization

For MCQ/MCQO questions, options are read aloud with their digit mapping:

```
"finya 1 kwa Ndiyo. finya 2 kwa Hapana. finya 3 kwa Nyingine."
```
(Translation: "press 1 for Yes. press 2 for No. press 3 for Other.")

---

## 9. Configuration Reference

### 9.1 Environment Variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TWILIO_ACCOUNT_SID` | Yes | -- | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Yes | -- | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Yes | -- | Twilio phone number (E.164) |
| `PUBLIC_BASE_URL` | Yes | -- | Public URL for webhooks (ngrok or custom) |
| `ADMIN_TOKEN` | No | `""` | Optional token for admin access without login |
| `AZURE_SPEECH_KEY` | Yes | -- | Azure Cognitive Services subscription key |
| `AZURE_SPEECH_REGION` | Yes | -- | Azure region (e.g., `eastus`) |
| `AZURE_TTS_VOICE_SW` | No | `sw-KE-ZuriNeural` | Swahili TTS voice name |
| `AZURE_TTS_VOICE_EN` | No | `en-US-JennyNeural` | English TTS voice name |
| `AZURE_TTS_FORMAT` | No | `audio-16khz-128kbitrate-mono-mp3` | Audio output format |
| `MAX_CALLS_PER_TICK` | No | `3` | Max concurrent calls per scheduler tick |
| `CALL_SPACING_SEC` | No | `0.8` | Delay between outbound calls |
| `FLASK_SECRET_KEY` | No | `CHANGE_ME_NOW` | Flask session signing key |
| `AUTO_START_NGROK` | No | `1` | Auto-start ngrok tunnel |
| `APP_OPEN_URL` | No | -- | Custom URL to open in browser |
| `OPEN_PUBLIC_URL` | No | `0` | Open ngrok URL instead of localhost |
| `AUTH_STATE_PATH` | No | `data/auth_state.json` | Auth state file location |
| `AUTH_LOG_PATH` | No | `data/auth_log.jsonl` | Auth event log location |
| `AUTH_MAX_FAILS` | No | `7` | Failed attempts before lockout |
| `AUTH_LOCK_SECONDS` | No | `900` | Lockout duration (seconds) |
| `AUTH_WINDOW_SECONDS` | No | `600` | Failure tracking window (seconds) |

### 9.2 Configuration File (`config.yaml`)

```yaml
# Twilio Configuration
twilio:
  account_sid: ""              # (Overridden by .env)
  auth_token: ""               # (Overridden by .env)
  from_number: ""              # (Overridden by .env)
  public_base_url: ""          # (Overridden by .env)

# IVR Configuration
ivr:
  questions_file: "data/questions.txt"    # Path to questions file
  gather_timeout_sec: 6                   # Seconds to wait for input
  speech_timeout: "auto"                  # Twilio auto speech detection
  say_voice: "alice"                      # Fallback Twilio voice
  speech_language: "sw-KE"                # Kiswahili-Kenya for recognition

# Audio Preprocessing (DeepFilterNet)
audio_processing:
  enabled: true                           # Toggle noise removal
  backend: "deepfilternet"                # Only supported backend
  processed_dir: "data/audio_processed"   # Cleaned audio output
  temp_dir: "data/audio_processed/tmp"    # Intermediate files
  output_sample_rate: 16000               # Whisper expects 16kHz
  model_sample_rate: 48000                # DeepFilterNet expects 48kHz
  channel_mode: "mixdown"                 # "mixdown" or "channel"
  caller_channel: 0                       # Channel index if mode="channel"
  keep_intermediate_files: false          # Cleanup temp files

# Authentication
auth:
  users:
    username:
      password_hash: "pbkdf2:sha256:..."  # Werkzeug generate_password_hash()
```

### 9.3 State Management Constants

| Constant | Value | Location | Description |
|----------|-------|----------|-------------|
| `MAX_ATTEMPTS` | `3` | `state.py` | Maximum call attempts per participant |
| `RETRY_GAP` | `1 hour` | `state.py` | Minimum time between retry attempts |
| `RECORDING_MAX_SEC` | `1800` (30 min) | `twilio_handler.py` | Maximum recording duration |
| `GATHER_TIMEOUT` | `6` seconds | `config.yaml` | DTMF/speech input timeout |
| `SCHEDULER_INTERVAL` | `15` seconds | `twilio_handler.py` | Scheduler polling interval |
| `WORKER_POLL` | `5` seconds | `background_worker.py` | Worker polling interval |
| `MAX_CHARS` | `3000` | `translate.py` | Max characters per translation chunk |

---

## 10. Admin Dashboard

### 10.1 UI Layout

```
+-----------------------------------------------------------------------+
| AudioSurvey AI -- Admin                           System: [RUNNING]   |
| NYC time: 2026-03-20 14:32:15 EDT    Logged in as: krishnanand        |
|                                                        [Sign out]     |
+-----------------------------------------------------------------------+
| [Dial Now] [Start] [Stop] [State Refresh] [Export Excel] [English]    |
|                                                                       |
| +-----------+ +-----------+ +-----------+ +-----------+               |
| |    42     | |    10     | |     5     | |    25     |               |
| |   Total   | |  Pending  | |In Progress| | Completed |               |
| +-----------+ +-----------+ +-----------+ +-----------+               |
+-----------------------------------------------------------------------+
| +---------------------+  +-----------------------------+              |
| |  Upload Contacts    |  |  Questions                  |              |
| |  [Choose CSV][Upload]|  |  +---------------------+   |              |
| |                     |  |  | INFO|Maswali kuhu...|   |              |
| |                     |  |  | OPEN|Tafadhali se...|   |              |
| |                     |  |  | MCQ|Question text...|   |              |
| |                     |  |  +---------------------+   |              |
| |                     |  |  [Save questions]           |              |
| +---------------------+  +-----------------------------+              |
+-----------------------------------------------------------------------+
| Conference Call                                                       |
| [+1...] [+1...] [Start call]                                         |
+-----------------------------------------------------------------------+
| Participants                                                          |
| +--------+----------+----------+----+----------+--------+--------+   |
| | ID     | Phone    | Status   |Att.| Engaged  |Sched.  |Schedule|   |
| +--------+----------+----------+----+----------+--------+--------+   |
| | P001   | +2****34 | Completed| 1  | Engaged  |03-15   |[__][Set]|  |
| | P002   | +2****56 | Pending  | 0  | Not eng. |        |[__][Set]|  |
| | P003   | +2****78 | Failed   | 3  | Not eng. |03-14   |[__][Set]|  |
| +--------+----------+----------+----+----------+--------+--------+   |
+-----------------------------------------------------------------------+
```

### 10.2 Live Polling Architecture

```
  BROWSER (JS)                FLASK SERVER            participants.json
       |                           |                        |
       +====[Every 1 second]=======================================+
       |                           |                        |      |
       |-- Check guards:          |                        |      |
       |   Skip if:               |                        |      |
       |   - Flatpickr open       |                        |      |
       |   - Schedule input dirty |                        |      |
       |   - Active focus in table|                        |      |
       |   - Previous poll active |                        |      |
       |                           |                        |      |
       |-- GET /admin/live_state ->|                        |      |
       |                           |-- load_participants -->|      |
       |                           |<-- JSON state ---------|      |
       |<-- {total, counts,        |                        |      |
       |     participants}         |                        |      |
       |                           |                        |      |
       |-- Update KPI cards       |                        |      |
       |-- Re-render table rows   |                        |      |
       |-- Re-initialize Flatpickr|                        |      |
       |                           |                        |      |
       +===========================================================+
```

### 10.3 Dashboard Features

| Feature | Description |
|---------|-------------|
| **Live NYC Clock** | JavaScript Intl.DateTimeFormat, updates every second |
| **KPI Cards** | Total, Pending, In Progress, Completed — live-updated |
| **Status Pills** | Color-coded badges: green=completed, yellow=in_progress, red=failed, gray=pending |
| **Engaged Badges** | Green dot = engaged, gray dot = not engaged |
| **Flatpickr Date Picker** | Dark-themed calendar with time selection and confirm plugin |
| **Dirty Input Detection** | Prevents live-poll from overwriting user's in-progress schedule edits |
| **File Upload** | Styled file input with chosen filename display |
| **Dark Theme** | Custom CSS with glassmorphism, radial gradients, and blur effects |

---

## 11. Background Services

### 11.1 Service Lifecycle

```
  MAIN THREAD              SCHEDULER THREAD         WORKER THREAD
       |                        |                        |
       |-- start_background_services()                   |
       |-- Thread(daemon).start -->|                     |
       |-- Thread(daemon).start ---|-------------------->|
       |-- app.run(port=5050)      |                     |
       |                           |                     |
       |    [Parallel execution]   |                     |
       |                           |                     |
       |          +===[Every 15 seconds]====+            |
       |          | load_participants()     |             |
       |          | Filter eligible         |             |
       |          |   (can_call)            |             |
       |          | client.calls.create()   |             |
       |          | mark_call_started()     |             |
       |          | save_participants()     |             |
       |          +=========================+             |
       |                                                  |
       |                    +===[Every 5 seconds]========+|
       |                    | load_participants()        ||
       |                    | Find processing_status     ||
       |                    |   = "pending"              ||
       |                    | Run ML pipeline            ||
       |                    | mark_completed()           ||
       |                    | save_participants()        ||
       |                    +============================+|
```

### 11.2 Call Eligibility Logic (`can_call`)

```
  can_call(state, pid, force)
       |
       v
  Participant exists?
       |          |
      No         Yes
       |          |
  [DENY]     Status is completed or failed?
                  |          |
                 Yes        No
                  |          |
             [DENY]     Attempts >= MAX_ATTEMPTS (3)?
                             |          |
                            Yes        No
                             |          |
                        [DENY]     force=True?
                                       |          |
                                      Yes        No
                                       |          |
                                  [ALLOW]    Has scheduled_time_utc?
                                                  |          |
                                                 No         Yes
                                                  |          |
                                             [DENY]     now_utc >= scheduled_time?
                                                             |          |
                                                            No         Yes
                                                             |          |
                                                        [DENY]     Last call time exists?
                                                                        |          |
                                                                       No         Yes
                                                                        |          |
                                                                   [ALLOW]   (now - last_call) >=
                                                                              RETRY_GAP (1h)?
                                                                                  |          |
                                                                                 No         Yes
                                                                                  |          |
                                                                             [DENY]     [ALLOW]
```

### 11.3 Worker Pipeline Stages

| Stage | Progress | Duration | Description |
|-------|----------|----------|-------------|
| 1. Prepare | 10-25% | ~5s | FFmpeg: extract channel, resample to 48kHz mono |
| 2. Denoise | 25-60% | ~30-60s | DeepFilterNet: neural noise removal (GPU if available) |
| 3. Resample | 60-75% | ~3s | FFmpeg: downsample to 16kHz for Whisper |
| 4. Transcribe | 75-85% | ~60-120s | Whisper large-v3: Swahili STT |
| 5. Translate | 85-93% | ~5-15s | Google Translate: chunked sw to en |
| 6. English TTS | 93-97% | ~5-10s | gTTS: English audio synthesis |
| 7. Complete | 100% | -- | Mark completed, save state |

---

## 12. Error Handling & Resilience

### 12.1 Fault Tolerance Matrix

| Component | Failure Mode | Handling Strategy |
|-----------|-------------|-------------------|
| **Twilio Call** | No answer / Busy | Mark `pending`, retry after 1h (up to 3 attempts) |
| **Twilio Call** | Failed / Canceled | Mark `failed` if max attempts reached |
| **Azure TTS** | API error | RuntimeError raised, prevents corrupted audio serving |
| **Azure TTS** | Duplicate request | Disk cache by content hash prevents re-synthesis |
| **Whisper** | Transcription drift | `condition_on_previous_text=False`, `temperature=0.0` |
| **Google Translate** | API error | 3 retries with 1.5s backoff; failed chunks marked with `[TRANSLATION_FAILED_CHUNK]` |
| **Google Translate** | Returns `None` | Explicit None check with RuntimeError |
| **DeepFilterNet** | Processing error | Graceful fallback to unprocessed audio |
| **Recording Download** | HTTP error | Logged, returns 200 (Twilio won't retry) |
| **State File** | Corrupt JSON | Renamed to `.corrupt`, returns empty state |
| **State File** | Concurrent access | `threading.RLock()` + atomic write (`.tmp` then `os.replace`) |
| **Scheduler** | Exception in tick | Caught and logged, loop continues |
| **Worker** | Exception in pipeline | Caught, `processing_status` set to `failed`, loop continues |
| **Auth State** | Missing file | Returns safe defaults `{"fails": {}, "locks": {}}` |
| **Config** | Missing `config.yaml` | Uses hardcoded defaults |

### 12.2 Retry Policy

```
  Call Placed (attempt #N)
       |
       v
  Call Result
       |
       +-- completed + engaged ---------> Status: completed
       |                                   Pipeline: triggered
       |
       +-- completed + NOT engaged -----> Status: pending
       |                                   (will retry in 1h)
       |
       +-- no-answer / busy -----------+
       |                               |
       +-- failed / canceled ----------+
                                       |
                                       v
                                  attempts >= 3?
                                       |          |
                                      Yes        No
                                       |          |
                                  Status:     Status: pending
                                  failed      (will retry in 1h)
                                  (no more
                                   retries)
```

---

## 13. Logging & Observability

### 13.1 Logging Architecture

| Log Type | Format | Location | Purpose |
|----------|--------|----------|---------|
| **Application Log** | Colored console | `stdout` | Real-time operational visibility |
| **Auth Event Log** | JSONL | `data/auth_log.jsonl` | Security audit trail |
| **Call Log** | CSV | `data/state/call_log.csv` | Call history and recording tracking |
| **Worker Progress** | Terminal progress bar | `stdout` | ML pipeline progress monitoring |

### 13.2 Console Log Format

```
[NYC 2026-03-20T14:32:15-04:00 | UTC 2026-03-20T18:32:15Z] PROMPT SENT | CallSid=CA123 | Participant=P001 | q3_mcq | Text="..."
```

### 13.3 Auth Event Log Format

```jsonl
{"event":"login","user":"krishnanand","ip":"127.0.0.1","login_utc":"2026-03-20T18:32:15Z","login_local":"2026-03-20 14:32:15 EDT","user_agent":"Mozilla/5.0..."}
{"event":"logout","user":"krishnanand","ip":"127.0.0.1","logout_utc":"2026-03-20T22:15:00Z","logout_local":"2026-03-20 18:15:00 EDT","session_duration_sec":13365}
```

### 13.4 Worker Progress Bar

```
[BackgroundWorker] participant=P001 | [################----]  80% | Removing background noise
```

### 13.5 Silenced Libraries

The following library loggers are suppressed to reduce noise:

`httpx`, `httpcore`, `httpcore.connection`, `httpcore.http2`, `hpack`, `hpack.hpack`, `h2`, `h2.connection`, `h2.config`, `gtts`, `gtts.tts`, `googletrans`, `urllib3`, `torio`, `torio._extension`, `torio._extension.utils`, `torchaudio`

---

## 14. Deployment Guide

### 14.1 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| pip | -- | Package management |
| ngrok | 3.x | HTTPS tunneling |
| FFmpeg | 4.x+ | Audio processing |
| Twilio Account | -- | Voice API |
| Azure Account | -- | Cognitive Services TTS |

### 14.2 Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/krishnanand20/audiosurvey_ai.git
cd audiosurvey_ai

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Twilio + Azure credentials

# 5. Launch (auto-starts ngrok + Flask + opens browser)
python3 run_app.py
```

### 14.3 Startup Sequence

```
  USER                run_app.py            ngrok             Flask App           BROWSER
   |                      |                   |                   |                   |
   |-- python3 run_app.py |                   |                   |                   |
   |                      |                   |                   |                   |
   |                      |-- Check AUTO_START_NGROK              |                   |
   |                      |-- Check existing tunnel               |                   |
   |                      |   (localhost:4040) |                   |                   |
   |                      |                   |                   |                   |
   |                      | [If no tunnel]    |                   |                   |
   |                      |-- Start ngrok --->|                   |                   |
   |                      |   http 5050       |                   |                   |
   |                      |                   |                   |                   |
   |                      | [Poll up to 20s]  |                   |                   |
   |                      |-- /api/tunnels -->|                   |                   |
   |                      |<-- HTTPS URL -----|                   |                   |
   |                      |                   |                   |                   |
   |                      |-- Set PUBLIC_BASE_URL env var         |                   |
   |                      |-- subprocess: python3 -m              |                   |
   |                      |   app.twilio_handler serve ---------->|                   |
   |                      |                   |                   |                   |
   |                      |                   |   Load .env, config.yaml              |
   |                      |                   |   Load Whisper model (large-v3)       |
   |                      |                   |   start_background_services()         |
   |                      |                   |   app.run(port=5050)                  |
   |                      |                   |                   |                   |
   |                      |-- Wait 1.5s       |                   |                   |
   |                      |-- Open browser ---|-------------------|------------------>|
   |                      |   http://127.0.0.1:5050/admin         |                   |
```

### 14.4 macOS DMG Distribution

The application can be packaged as a native macOS `.app` inside a DMG installer:

```bash
cd packaging/macos_dmg
./build_macos_dmg.sh
# Output: output/AudioSurvey-AI.dmg
```

**Build process:**
1. Compiles Swift icon generator, generates 1024x1024 PNG icon
2. Creates `.iconset` with all required sizes via `sips`
3. Converts to `.icns` via `iconutil`
4. Builds `.app` bundle with `Info.plist`, launcher script, and project files
5. Creates read-write DMG, sets volume icon, converts to compressed DMG
6. Optionally embeds icon resource via `Rez`

**App bundle structure:**
```
AudioSurvey AI.app/
  Contents/
    Info.plist
    MacOS/
      AudioSurveyAI    (bash launcher)
    Resources/
      AppIcon.icns
      project/          (full project copy)
```

---

## 15. Directory Structure

```
audiosurvey_ai/
|
|-- .env                          # Environment variables (secrets -- gitignored)
|-- .gitignore                    # Git exclusion rules
|-- config.yaml                   # Application configuration
|-- main.py                       # Batch processing entry point
|-- run_app.py                    # Application launcher (ngrok + Flask)
|-- requirements.txt              # Python dependencies
|-- README.md                     # Quick-start documentation
|-- DOCUMENTATION.md              # This file
|
|-- app/                          # Application source code
|   |-- twilio_handler.py         # Flask app, IVR routes, Azure TTS, auth
|   |-- dashboard.py              # Admin dashboard UI + routes
|   |-- state.py                  # Thread-safe state management
|   |-- scheduler.py              # Background call scheduler
|   |-- background_worker.py      # ML processing pipeline worker
|   |-- audio_preprocess.py       # DeepFilterNet noise removal
|   |-- transcribe.py             # Whisper speech-to-text
|   |-- translate.py              # Google Translate integration
|   |-- tts.py                    # Google TTS (English audio)
|   |-- azure_tts.py              # Azure Cognitive Services TTS
|   |-- export_excel.py           # Excel response export
|   |-- auth.py                   # Authentication helpers
|   |-- utils.py                  # Scheduling utilities
|   |-- file_naming.py            # Safe filename generation
|   |-- logger.py                 # Colored logging setup
|   |-- runtime_warnings.py       # Warning suppression
|   |-- twilio_utils.py           # Twilio call helpers
|
|-- data/                         # Runtime data (mostly gitignored)
|   |-- questions.txt             # Survey questions (pipe-delimited)
|   |-- state/                    # Participant state + logs
|   |   |-- participants.json     # Participant records
|   |   |-- call_log.csv          # Call history
|   |   |-- settings.json         # System settings
|   |-- audio/                    # Raw call recordings (.wav)
|   |-- audio_processed/          # Denoised recordings (.wav)
|   |-- transcripts/              # Whisper transcriptions (.txt)
|   |-- translations/             # English translations (.txt)
|   |-- english_audio/            # English TTS audio (.mp3)
|   |-- ivr_audio/                # Cached IVR prompts (.mp3)
|   |-- results/                  # Excel exports (.xlsx)
|   |-- *.csv                     # Contact lists
|
|-- packaging/                    # Distribution packaging
    |-- macos_icon_generator.swift # Programmatic icon generation
    |-- macos_dmg/
        |-- build_macos_dmg.sh    # DMG build script
        |-- README.md             # Build instructions
        |-- output/
            |-- AudioSurvey-AI.dmg # Built DMG installer
```

---

## 16. Dependency Matrix

### 16.1 Core Dependencies

| Package | Version | Purpose | Critical? |
|---------|---------|---------|-----------|
| `Flask` | 3.1.2 | Web framework | Yes |
| `twilio` | 9.10.0 | Telephony API | Yes |
| `openai-whisper` | 20240930 | Speech-to-text | Yes |
| `azure-cognitiveservices-speech` | 1.48.1 | Neural TTS (prompts) | Yes |
| `googletrans` | 4.0.0rc1 | Translation (sw to en) | Yes |
| `gTTS` | 2.5.4 | English audio generation | Yes |
| `deepfilternet` | 0.5.6 | Background noise removal | Medium |
| `torch` | 2.8.0 | ML framework (Whisper + DeepFilterNet) | Yes |
| `torchaudio` | 2.8.0 | Audio tensor operations | Yes |

### 16.2 Data & Export

| Package | Version | Purpose |
|---------|---------|---------|
| `pandas` | 2.3.3 | DataFrame operations for Excel export |
| `openpyxl` | 3.1.5 | Excel file writing |
| `numpy` | 1.26.4 | Numerical operations |
| `pydub` | 0.25.1 | Audio manipulation |

### 16.3 Infrastructure

| Package | Version | Purpose |
|---------|---------|---------|
| `python-dotenv` | 1.2.1 | .env file loading |
| `PyYAML` | 6.0.3 | config.yaml parsing |
| `gunicorn` | 23.0.0 | Production WSGI server |
| `Werkzeug` | 3.1.4 | Password hashing, HTTP utilities |
| `colorlog` | 6.10.1 | Colored console logging |
| `requests` | 2.32.5 | HTTP client (recording download) |
| `Jinja2` | 3.1.6 | Template rendering |

### 16.4 External Services

| Service | Provider | Purpose | Pricing Model |
|---------|----------|---------|---------------|
| **Voice API** | Twilio | Outbound/inbound calls, recording, DTMF/speech gather | Per-minute |
| **Speech TTS** | Azure Cognitive Services | Neural TTS for IVR prompts (Swahili + English) | Per-character |
| **Translation** | Google Translate | Kiswahili to English translation | Free (scraping) |
| **Text-to-Speech** | Google TTS (gTTS) | English audio from translations | Free |
| **Tunneling** | ngrok | HTTPS tunnel for Twilio webhooks | Free tier available |

---

## 17. Glossary

| Term | Definition |
|------|-----------|
| **IVR** | Interactive Voice Response — automated phone menu system |
| **DTMF** | Dual-Tone Multi-Frequency — keypad tones (pressing 1-9, *, #) |
| **TwiML** | Twilio Markup Language — XML instructions for call handling |
| **TTS** | Text-to-Speech — converting text to spoken audio |
| **STT** | Speech-to-Text — converting spoken audio to text |
| **E.164** | International phone number format (e.g., `+254700000000`) |
| **CallSid** | Unique Twilio identifier for a phone call |
| **SSML** | Speech Synthesis Markup Language — XML for controlling TTS output |
| **DeepFilterNet** | Neural network for real-time speech enhancement/noise removal |
| **Whisper** | OpenAI's multilingual speech recognition model |
| **MCQ** | Multiple Choice Question (DTMF input) |
| **MCQO** | Multiple Choice Question with "Other" (DTMF + optional speech) |
| **OPEN** | Open-ended question (speech input) |
| **INFO** | Informational prompt (no input collected) |
| **Engaged** | Participant spoke during the call (real speech detected) |
| **NYC / NY_TZ** | New York City timezone (America/New_York) used for scheduling |
| **ngrok** | Tunneling service exposing localhost to the internet |
| **Kiswahili / sw** | Swahili language (ISO 639-1: `sw`) |
| **sw-KE** | Swahili as spoken in Kenya (BCP 47 locale tag) |
| **Pipeline** | The 4-stage ML processing chain: denoise, transcribe, translate, TTS |
| **Participant** | A survey respondent identified by `participant_id` |
| **Flatpickr** | JavaScript date/time picker library used in the dashboard |
| **PII** | Personally Identifiable Information (phone numbers, names) |
| **PBKDF2** | Password-Based Key Derivation Function 2 (hashing algorithm) |

---

<p align="center">
  <em>End of Document</em><br/>
  <code>AudioSurvey AI v1.1.0</code> &nbsp;|&nbsp; <code>Generated 2026-03-20</code>
</p>
