<div style="background:#ffffff;padding:56px 64px;box-sizing:border-box;">

<div style="border-top:4px solid #2563eb;margin-bottom:48px;"></div>

<div style="font-size:9.5pt;letter-spacing:5px;color:#2563eb;text-transform:uppercase;font-weight:600;margin-bottom:14px;">AI Research Technology Platform</div>

<div style="font-size:48pt;font-weight:900;color:#0f172a;letter-spacing:-2px;line-height:1;margin-bottom:8px;">AudioSurvey AI</div>

<div style="height:4px;width:320px;background:linear-gradient(90deg,#2563eb,#7c3aed,rgba(124,58,237,0));margin:18px 0 22px 0;"></div>

<div style="font-size:19pt;color:#1d4ed8;font-weight:300;letter-spacing:0.5px;margin-bottom:4px;">Technical Architecture &amp; System Documentation</div>
<div style="font-size:11pt;color:#475569;margin-bottom:48px;">Comprehensive reference for system design, APIs, data models, and operations</div>

<table style="border-collapse:collapse;width:100%;max-width:600px;margin-bottom:40px;">
  <tr style="border-bottom:1px solid #e2e8f0;">
    <td style="padding:12px 0;color:#94a3b8;font-size:9.5pt;text-transform:uppercase;letter-spacing:1.5px;width:180px;">Document Version</td>
    <td style="padding:12px 24px;font-size:12pt;font-weight:700;color:#1e293b;border-left:3px solid #2563eb;">1.2.0</td>
  </tr>
  <tr style="border-bottom:1px solid #e2e8f0;">
    <td style="padding:12px 0;color:#94a3b8;font-size:9.5pt;text-transform:uppercase;letter-spacing:1.5px;">Release Date</td>
    <td style="padding:12px 24px;font-size:12pt;font-weight:700;color:#1e293b;border-left:3px solid #2563eb;">April 6, 2026</td>
  </tr>
  <tr style="border-bottom:1px solid #e2e8f0;">
    <td style="padding:12px 0;color:#94a3b8;font-size:9.5pt;text-transform:uppercase;letter-spacing:1.5px;">Author</td>
    <td style="padding:12px 24px;font-size:12pt;font-weight:700;color:#1e293b;border-left:3px solid #2563eb;">Krishnanand</td>
  </tr>
  <tr style="border-bottom:1px solid #e2e8f0;">
    <td style="padding:12px 0;color:#94a3b8;font-size:9.5pt;text-transform:uppercase;letter-spacing:1.5px;">Project Status</td>
    <td style="padding:12px 24px;font-size:12pt;font-weight:700;color:#059669;border-left:3px solid #10b981;">Completed</td>
  </tr>
  <tr style="border-bottom:1px solid #e2e8f0;">
    <td style="padding:12px 0;color:#94a3b8;font-size:9.5pt;text-transform:uppercase;letter-spacing:1.5px;">Classification</td>
    <td style="padding:12px 24px;font-size:12pt;font-weight:700;color:#dc2626;border-left:3px solid #ef4444;"><strong>Confidential — Restricted Distribution</strong></td>
  </tr>
  <tr>
    <td style="padding:12px 0;color:#94a3b8;font-size:9.5pt;text-transform:uppercase;letter-spacing:1.5px;">Core Stack</td>
    <td style="padding:12px 24px;font-size:10.5pt;font-weight:600;color:#1d4ed8;border-left:3px solid #2563eb;">Python · Flask · Twilio · Azure Cognitive Services · OpenAI Whisper · PyTorch</td>
  </tr>
</table>

<div style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:10px;padding:26px 30px;max-width:680px;">
  <div style="font-size:9pt;letter-spacing:2.5px;color:#2563eb;text-transform:uppercase;font-weight:600;margin-bottom:10px;">Abstract</div>
  <p style="color:#334155;font-size:11pt;line-height:1.75;margin:0;">AudioSurvey AI is an AI-powered multilingual Interactive Voice Response (IVR) survey platform designed for academic and public health field research. The system conducts fully automated telephone surveys in Kiswahili, targeting African refugee populations, through a combination of Twilio cloud telephony, Azure Neural Text-to-Speech, OpenAI Whisper speech recognition, and a four-stage ML post-processing pipeline comprising noise removal, transcription, translation, and English audio generation. Survey data is exported to structured Excel workbooks for analysis. The platform is managed via a secure web-based admin dashboard with real-time participant tracking, scheduled outbound calling, inbound call handling, and conference call capabilities.</p>
</div>

<div style="margin-top:50px;border-top:1px solid #e2e8f0;padding-top:18px;display:flex;justify-content:space-between;font-size:9pt;">
  <span style="color:#64748b;">AudioSurvey AI Research Platform</span>
  <span style="color:#64748b;">Technical Architecture &amp; System Documentation · v1.2.0</span>
  <span style="color:#64748b;">© 2026 · All Rights Reserved</span>
</div>
<div style="border-bottom:4px solid #2563eb;margin-top:14px;"></div>

</div>

<div style="page-break-after:always;"></div>

# Project Documentation

## Revision History

| Version | Date | Author | Change Description |
|---------|------|--------|--------------------|
| 0.1.0 | 2026-01-22 | Krishnanand | Initial project setup — TTS, transcription, and translation modules scaffolded |
| 0.2.0 | 2026-01-22 | Krishnanand | IVR pipeline operational — inbound and outbound calling working end-to-end |
| 0.3.0 | 2026-01-22 | Krishnanand | Security improvements — `.env` for secrets, safe config template added |
| 0.4.0 | 2026-01-23 | Krishnanand | README added, contacts CSV excluded from version control |
| 0.5.0 | 2026-01-26 | Krishnanand | State management, call logs, and caller handler functions updated |
| 0.6.0 | 2026-02-22 | Krishnanand | 5-March calling milestone — initial full call flow verified |
| 1.0.0 | 2026-02-22 | Krishnanand | **First stable release** — core IVR engine, Twilio integration, Whisper STT, admin dashboard |
| 1.0.1 | 2026-02-26 | Krishnanand | Excel export support for survey responses |
| 1.0.2 | 2026-03-01 | Krishnanand | Excel formatting corrections, UX/UI upgrade, audio channel fix for full-call recordings |
| 1.0.3 | 2026-03-03 | Krishnanand | Updated survey questions, system cleanup |
| 1.0.4 | 2026-03-04 | Krishnanand | English translation export, "Convert to English" button added to dashboard |
| 1.0.5 | 2026-03-05 | Krishnanand | Authentication system — login/logout, PBKDF2 password hashing, brute-force protection, session management |
| 1.0.6 | 2026-03-05 | Krishnanand | Full call testing milestone — results saved and verified end-to-end |
| 1.0.7 | 2026-03-08 | Krishnanand | MCQO digit bug fix, hardcoded button logic corrected |
| 1.0.8 | 2026-03-10 | Krishnanand | DeepFilterNet background noise removal integrated, random crash fix, log improvements |
| 1.0.9 | 2026-03-15 | Krishnanand | macOS DMG packaging, icon generator update |
| 1.1.0 | 2026-03-17 | Krishnanand | File naming convention refactored for clarity; auth info cleanup; DOCUMENTATION.md created |
| 1.1.1 | 2026-03-21 | Krishnanand | Full audio recording logic redesigned — recording now starts at `/voice` entry, not after survey completion |
| 1.1.2 | 2026-04-01 | Krishnanand | Study guide and presentation documentation added (`STUDY_GUIDE.md`) |
| 1.1.3 | 2026-04-05 | Krishnanand | Inbound call response collection — inbound callers now matched to participants and routed through full survey + export flow |
| 1.1.4 | 2026-04-05 | Krishnanand | Call direction tracking — `direction` field added to call log and dashboard display (`Incoming` / `Outgoing`) |
| 1.2.0 | 2026-04-06 | Krishnanand | **Major release** — improved inbound call handling, auto participant creation for unknown callers, per-call End Call controls, End All Calls, live tech info panel, `runtime_status.py` module, redesigned login page, safer call/export state updates |

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
| 12 | [Inbound Call Handling](#12-inbound-call-handling) | Inbound caller routing, participant matching, direction tracking |
| 13 | [Error Handling & Resilience](#13-error-handling--resilience) | Fault tolerance, retry logic, graceful degradation |
| 14 | [Logging & Observability](#14-logging--observability) | Logging architecture, runtime status, audit trails |
| 15 | [Deployment Guide](#15-deployment-guide) | Local setup, ngrok tunneling, macOS DMG packaging |
| 16 | [Directory Structure](#16-directory-structure) | Complete project tree with annotations |
| 17 | [Dependency Matrix](#17-dependency-matrix) | Third-party libraries and their roles |
| 18 | [Glossary](#18-glossary) | Domain terminology and abbreviations |

---

## 1. Executive Summary

### 1.1 Purpose

AudioSurvey AI is an AI-powered multilingual Interactive Voice Response (IVR) survey platform designed to conduct automated voice-based research surveys over telephone calls. The system targets **African refugees who speak Kiswahili**, enabling researchers to collect structured survey responses at scale without requiring in-person enumerators.

### 1.2 Business Context

The platform was built for academic and public health research. It is designed as a **flexible, multi-survey system** — the survey topic, questions, and thematic sections are fully configurable via the `data/questions.txt` file. Researchers can deploy different surveys for different studies without any code changes. Both outbound scheduled calling and inbound participant-initiated calls are fully supported, routing through the same survey and ML processing pipeline.

### 1.3 Key Capabilities

| Capability | Description |
|------------|-------------|
| **Automated Outbound Calling** | Scheduled batch dialing of research participants via Twilio |
| **Inbound Call Support** | Participants can call in; auto-matched to existing records or auto-created |
| **Call Direction Tracking** | All calls tagged as `inbound` or `outbound-api`, shown in dashboard |
| **Multilingual IVR** | Survey prompts spoken in Kiswahili via Azure Neural TTS |
| **Multi-Format Questions** | INFO, OPEN (speech), MCQ (DTMF keypad), MCQO (MCQ + "Other" speech) |
| **Full-Call Recording** | Complete audio capture of every call (up to 30 minutes) |
| **AI Audio Processing** | Background noise removal via DeepFilterNet |
| **Speech-to-Text** | Post-call transcription using OpenAI Whisper (large-v3) |
| **Machine Translation** | Automatic Kiswahili to English translation |
| **English Audio Generation** | TTS synthesis of translated responses |
| **Structured Data Export** | Excel export of MCQ/MCQO responses (original + English) |
| **Admin Dashboard** | Real-time web UI — participant management, live status, call controls |
| **Per-Call & Global Call Controls** | End individual calls or all active calls from the admin UI |
| **Conference Calling** | Three-way call support for researcher-moderated interviews |
| **Runtime Status Panel** | Live tech info — scheduler status, worker status, system load |
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
| **Runtime Monitoring** | `runtime_status.py` (heartbeat-based) |
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
|   | Conference   |  | Excel Export |  | Inbound Call |                |
|   | Call Module  |  |              |  | Handler      |                |
|   +--------------+  +--------------+  +--------------+                |
|                                                                       |
|   +-----------------------------+  +-----------------------------+    |
|   |     BACKGROUND SERVICES     |  |   RUNTIME STATUS MODULE     |    |
|   |  +----------+ +-----------+ |  |  Scheduler & Worker         |    |
|   |  | Scheduler| | ML Worker | |  |  heartbeat tracking         |    |
|   |  | (15s)    | | (5s poll) | |  |                             |    |
|   |  +----------+ +-----------+ |  +-----------------------------+    |
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

- Participant Phone (outbound or inbound) <--> Twilio <--> ngrok <--> IVR Webhook Handlers
- Inbound callers matched to participants by phone or auto-created
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
|   PSTN/VoIP (outbound or inbound)         | HTTPS                |
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
|    mark_scheduler_heartbeat()  mark_worker_heartbeat()           |
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
       runtime_status.py

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
               runtime_status.py (Heartbeat Monitoring)  [NEW v1.2.0]
```

### 3.2 Module Descriptions

| Module | Lines | Responsibility |
|--------|-------|---------------|
| `twilio_handler.py` | ~1,780 | Core Flask application. IVR webhook routes, inbound call matching, Azure TTS, auth, conference calling, recording download, call controls, Excel export trigger, application bootstrap. Central orchestrator. |
| `dashboard.py` | ~1,280 | Admin web dashboard. HTML UI with inline CSS/JS. Participant management, live-polling, scheduling, pause/resume, state reset, call controls (End Call, End All), live tech status panel. |
| `runtime_status.py` | ~92 | Background service health tracking. Heartbeat-based scheduler and worker status reporting. Exposes `get_runtime_snapshot()` for dashboard live info. |
| `state.py` | ~241 | Thread-safe participant state management. JSON persistence with atomic writes, call eligibility logic (`can_call`), state transitions, retry gap enforcement, participant schema migration. |
| `export_excel.py` | ~314 | Builds structured Excel exports from participant responses. Decodes DTMF digits back to option text, filters OPEN responses, supports original-language and English-translated exports. |
| `background_worker.py` | ~148 | Continuous polling worker that processes completed recordings through the 4-stage ML pipeline (denoise → transcribe → translate → TTS). Terminal progress bars and heartbeat updates. |
| `scheduler.py` | ~114 | Timed call dispatcher. Runs every 15 seconds, checks participant eligibility, places Twilio calls. Supports force-dial mode. Updates scheduler heartbeat. |
| `audio_preprocess.py` | ~210 | Audio noise removal pipeline using DeepFilterNet. FFmpeg-based channel extraction/resampling, PyTorch noise removal, output resampling for Whisper. |
| `transcribe.py` | ~48 | Whisper large-v3 speech-to-text. Swahili language hint, returns text and detected language. Single-file and directory batch modes. |
| `translate.py` | ~134 | Chunked Google Translate integration. Splits on sentence boundaries, retries failed chunks, marks failures with placeholder tags. |
| `tts.py` | ~55 | Google TTS (gTTS) wrapper for generating English MP3 audio from translated text. |
| `auth.py` | ~165 | Authentication helpers. Brute-force protection, session management, credential verification. |
| `utils.py` | ~25 | Scheduling utility. Converts NYC local time to UTC and updates participant state. |
| `azure_tts.py` | ~49 | Standalone Azure TTS module with SHA1 disk caching. Generates IVR call prompt audio. |
| `file_naming.py` | ~28 | Safe filename generation. Sanitizes participant IDs, generates timestamped base names. |
| `logger.py` | ~76 | Colored console logging via `colorlog`. Silences noisy third-party library logs. Context manager for quiet operations. |
| `runtime_warnings.py` | ~16 | Suppresses urllib3/OpenSSL compatibility warnings at startup. |
| `run_app.py` | ~129 | Application launcher. Auto-starts ngrok, sets environment variables, launches Flask subprocess, opens browser. |
| `main.py` | ~28 | Standalone batch processor for offline audio → transcript → translation → TTS pipeline. |

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
    |                      |    | mark_scheduler_heartbeat()   |
    |                      |    | load_participants()  |       |
    |                      |    | can_call() check     |       |
    |                      |    +----------------------+       |
    |                      |                  |                 |
    |                      |                  |-- calls.create --->
    |                      |                  |-- mark_call_started()
    |                      |                  |                 |

  TWILIO             PARTICIPANT          IVR HANDLER       AZURE TTS
    |                      |                  |                 |
    |-- Ring ------------->|                  |                 |
    |<-- Answer -----------|                  |                 |
    |-- POST /voice --------------------->|   direction=outbound|
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

### 4.2 Inbound Call Lifecycle (v1.2.0)

```
  PARTICIPANT           TWILIO             IVR HANDLER        STATE
    |                      |                   |                 |
    |-- Dials Twilio #---->|                   |                 |
    |                      |-- POST /voice --->|                 |
    |                      |   From=+254...    |                 |
    |                      |   Direction=inbound                 |
    |                      |                   |                 |
    |                      |        Match caller by phone?       |
    |                      |              |          |           |
    |                      |             Yes         No          |
    |                      |              |          |           |
    |                      |         Use existing   Auto-create  |
    |                      |         participant    new participant
    |                      |         record         from caller # |
    |                      |              |          |           |
    |                      |              +----+-----+           |
    |                      |                   |                 |
    |                      |              mark_call_started()    |
    |                      |              (direction=inbound)    |
    |                      |                   |                 |
    |                      | [Same IVR flow as outbound]         |
    |                      |   /start, /next, /mcq-handler, etc. |
    |                      |                   |                 |
    |                      |-- POST /call-status               |
    |                      |-- POST /recording-done            |
    |                      |              append_to_excel()     |
    |                      |              processing = pending  |
```

### 4.3 ML Processing Pipeline

```
 INPUT         STAGE 1               STAGE 2        STAGE 3           STAGE 4     OUTPUTS
            Audio Preprocessing   Transcription   Translation       English TTS

+-------+  +---------------+    +-----------+  +-------------+  +---------+  +-----------+
| Raw   |  | FFmpeg        |    |           |  | Language    |  |         |  | Cleaned   |
| WAV   |->| Channel Mix + |    |           |  | Detection   |  |         |  | WAV       |
|       |  | Resample 48kHz|    |           |  |   |         |  |         |  +-----------+
+-------+  +-------+-------+    |           |  |lang=en lang |  |         |  | Transcript|
                   |             |           |  |  |    !=en  |  |         |  | .txt (sw) |
           +-------+-------+    | Whisper   |  |  v      v   |  |         |  +-----------+
           | DeepFilterNet |    | large-v3  |  | Copy  Chunk |  |         |  | Translation
           | Noise Removal |    | lang="sw" |->| as-is  3000 |->| gTTS    |  | .txt (en) |
           | (PyTorch)     |    | temp=0.0  |  | (en)  chars |  | lang=en |  +-----------+
           +-------+-------+    | fp16=False|  |  |    |     |  |         |  | English   |
                   |             +-----------+  |  |  Translate  |         |  | .mp3      |
           +-------+-------+                   |  |  3 retries  +---------+  +-----------+
           | FFmpeg        |                   |  +------+------+
           | Resample 16kHz|                   +---------|------+
           +---------------+                             v
                                                  data/translations/
```

### 4.4 Recording Callback Flow

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
                   (saved)         (no-answer/busy/failed/canceled)
                                       |           |
                                      Yes         No
                                       |           |
                                  Skip pipeline  Participant engaged?
                                                   |           |
                                                  No          Yes
                                                   |           |
                                             Skip pipeline   Download WAV from Twilio
                                             (saved_no_engagement)  |
                                                            Save to data/audio/
                                                                 |
                                                            Set processing_status = pending
                                                                 |
                                                            Log to call_log.csv
                                                                 |
                                                            Background Worker picks up
```

### 4.5 Excel Export Data Flow

```
  INPUT                         PROCESSING                         OUTPUT

  +---------------+     +---------------------+     +---------------------------+
  | questions.txt |---->| Build Response      |     | ivr_responses.xlsx        |
  +---------------+     | Metadata            |     | (Kiswahili option text)   |
                        +----------+----------+     +-------------+-------------+
  +-----------------+              |                               |
  | participants.json|-->| Filter Responses   |     Cell-by-cell translate
  +-----------------+   | (exclude OPEN)      |                    |
                        +----------+----------+     +-------------+-------------+
                                   |                | Translation Cache (dict)  |
                        +----------+----------+     +-------------+-------------+
                        | Decode DTMF         |                    |
                        | digit -> Option Text|     +-------------+-------------+
                        +----------+----------+     | ivr_responses_english.xlsx|
                                   |                +---------------------------+
                        +----------+----------+
                        | Renumber Question   |
                        | Keys (q1, q2, ...)  |
                        +----------+----------+
                                   |
                        +----------+----------+
                        | Build DataFrame     |-------> ivr_responses.xlsx
                        +---------------------+
```

---

## 5. API Reference

### 5.1 Public Endpoints (No Auth Required)

These endpoints are accessible without authentication — called by Twilio webhooks or used for health checks.

#### `POST /voice`
> **Call Entrypoint — Outbound and Inbound**

Initiates full-call recording and redirects to the survey start. For inbound calls, attempts to match the caller by phone number or auto-creates a participant.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `CallSid` | Twilio | Unique call identifier |
| `From` | Twilio | Caller phone number (used for inbound matching) |
| `Direction` | Twilio | `inbound` or `outbound-api` |

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

Processes keypad digit. If MCQO and "Other" selected, redirects to speech capture.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `q` | Query string | Question index |
| `Digits` | Twilio | Pressed DTMF digit (1–9) |
| `CallSid` | Twilio | Call identifier |

**Response:** TwiML — next question or `/mcqo-other-handler`

---

#### `POST /mcqo-other-handler?q={index}`
> **MCQO "Other" Speech Handler**

Captures the free-speech "Other" response and moves to next question.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `q` | Query string | Question index |
| `SpeechResult` | Twilio | Free-speech "Other" response |

**Response:** TwiML — redirects to `/next?q={q+1}`

---

#### `POST /call-status`
> **Twilio Call Status Webhook**

Receives call completion events. Updates participant state, triggers Excel export on completion.

| Parameter | Source | Description |
|-----------|--------|-------------|
| `CallSid` | Twilio | Call identifier |
| `CallStatus` | Twilio | `completed`, `no-answer`, `busy`, `failed`, `canceled` |

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
| `Direction` | Twilio | `inbound` or `outbound-api` |

**Response:** `200 OK`

---

#### `GET /health`
> **Health Check**

**Response:** `200 OK` — body: `ok`

---

#### `POST /conference_host`, `POST /conference_join`, `POST /conference_ivr`, `POST /conference_ivr_next`
> **Conference Call Endpoints**

Three-way conference call flow. Host hears IVR questions while waiting; conference starts when questions complete.

---

#### `POST /silence`
> **Silence Generator**

Returns TwiML with a 60-second pause — used as conference hold fallback.

---

#### `GET /ivr-audio/<filename>`
> **Static IVR Audio Server**

Serves cached Azure TTS audio from `data/ivr_audio/`.

---

### 5.2 Authenticated Endpoints (Login Required)

All `/admin/*` routes require an active session or valid `ADMIN_TOKEN` query parameter.

#### `GET /admin` — Admin Dashboard (full HTML page)

#### `GET /admin/live_state` — Live State JSON API

```json
{
  "total": 42,
  "counts": {"pending": 10, "in_progress": 5, "completed": 25, "failed": 2},
  "participants": [
    {
      "participant_id": "P001",
      "phone_masked": "+2******1234",
      "status": "completed",
      "attempts": 1,
      "engaged": true,
      "direction": "inbound",
      "scheduled_local": "2026-04-05 14:00",
      "processing_status": "completed"
    }
  ],
  "runtime": {
    "scheduler": {"status": "running", "label": "Running", "age_sec": 3},
    "worker": {"status": "running", "label": "Running", "age_sec": 2}
  }
}
```

#### `POST /admin/upload_contacts` — Upload participant CSV (`participant_id,phone_e164`)

#### `POST /admin/save_questions` — Save `data/questions.txt`

#### `POST /admin/schedule` — Set scheduled call time for a participant (NYC timezone)

#### `POST /admin/dial_now` — Force dial all eligible participants immediately

#### `POST /admin/pause` / `POST /admin/resume` — Toggle scheduler pause

#### `POST /admin/reset_state` — Back up and reset all participant state

#### `GET /admin/export_excel` — Download `ivr_responses.xlsx` (original language)

#### `GET /admin/export_excel_english` — Download `ivr_responses_english.xlsx` (translated)

#### `POST /admin/conference_call` — Dial two numbers into a conference room

#### `POST /admin/end_call` — End a specific active call by CallSid *(v1.2.0)*

#### `POST /admin/end_all_calls` — End all currently active calls *(v1.2.0)*

---

### 5.3 Authentication Endpoints

#### `GET /login` — Login page

#### `POST /login` — Authenticate; sets session cookie on success

#### `POST /logout` — Clear session and log event

---

## 6. Data Models & State Schema

### 6.1 Participant Schema

```json
{
  "P001": {
    "status": "completed",
    "attempts": 1,
    "last_call_time": "2026-04-05T18:30:00",
    "last_call_sid": "CA1234567890abcdef",
    "last_call_status": "completed",
    "engaged": true,
    "last_recording_url": "https://api.twilio.com/2010-04-01/Accounts/.../Recordings/RE...",
    "last_outputs": {},
    "scheduled_time_local": "2026-04-05 14:30",
    "scheduled_time_utc": "2026-04-05T18:30:00Z",
    "phone_e164": "+254700000000",
    "responses": {
      "q1": "Jina langu ni Amina",
      "q2": "2",
      "q3": "1",
      "survey_q_counter": 15
    },
    "processing_status": "completed",
    "audio_path": "data/audio/P001_20260405_183000.wav",
    "recording_url": "https://api.twilio.com/...",
    "direction": "inbound"
  }
}
```

### 6.2 Participant State Machine

```
                       +-------+
                       | START |
                       +---+---+
                           |
                       CSV upload / inbound call
                           |
                           v
                       +-------+
                +----->| idle  |
                |      +---+---+
                |          |
                |     Schedule set / inbound triggers
                |          |
                |          v
                |    +---------+       Eligible when:
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
           |      +-----------+                    (retry)
           +      | completed |
                  +-----------+

     No answer/Busy (attempts >= 3)
           |
           v
      +--------+
      | failed |
      +--------+
```

### 6.3 Processing Status State Machine

```
  Recording received
        |
        v
  Engaged?
  |         |
 No         Yes
  |         |
saved_no_  pending
engagement  |
           Worker picks up
            |
            v
        processing
            |
       +----+----+
       |         |
    success    error
       |         |
  completed   failed
```

### 6.4 Call Log Schema

`data/state/call_log.csv`:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp_utc` | ISO 8601 | Event timestamp |
| `participant_id` | String | Participant identifier |
| `phone_masked` | String | Masked phone (e.g., `+2******1234`) |
| `direction` | String | `inbound` or `outbound-api` |
| `call_sid` | String | Twilio call SID |
| `recording_url` | URL | Twilio recording URL |
| `audio_path` | String | Local WAV file path |
| `transcript_path` | String | Kiswahili transcript path |
| `translation_path` | String | English translation path |
| `english_audio_path` | String | English MP3 path |

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
{ "paused": false }
```

---

## 7. Authentication & Security

### 7.1 Authentication Flow

```
  USER                  FLASK              config.yaml     auth_state.json  auth_log.jsonl
   |                       |                    |                |                |
   |-- GET /admin -------->|                    |                |                |
   |                       |-- before_request   |                |                |
   |<-- 302 -> /login -----|   guard            |                |                |
   |                       |                    |                |                |
   |-- POST /login ------->|                    |                |                |
   |  (username,password)  |                    |                |                |
   |                       |-- _is_locked? -----|--------------->|                |
   |                       |                    |                |                |
   |          [If Locked]  |                    |                |                |
   |<-- "Try again in Xs"--|                    |                |                |
   |                       |                    |                |                |
   |                       |-- Load auth.users->|                |                |
   |                       |-- check_password_hash()             |                |
   |                       |                    |                |                |
   |          [If Invalid] |-- _record_fail() --|--------------->|                |
   |                       |   (7 fails=lock)   |                |                |
   |<-- "Invalid creds"    |-- Log event -------|----------------|--------------->|
   |                       |                    |                |                |
   |          [If Valid]   |-- _clear_fails() --|--------------->|                |
   |                       |-- Set session      |                |                |
   |                       |-- Log success -----|----------------|--------------->|
   |<-- 302 -> /admin -----|                    |                |                |
```

### 7.2 Security Measures

| Measure | Implementation | Details |
|---------|---------------|---------|
| **Password Hashing** | PBKDF2-SHA256 | 1,000,000 iterations via Werkzeug |
| **Brute-Force Protection** | Rate limiting per username+IP | 7 failures in 10 min → 15-min lockout |
| **Session Security** | Flask sessions | `HttpOnly`, `SameSite=Lax`, `Secure=True`, 8-hour lifetime |
| **Phone Masking** | `mask_phone()` | First 2 + last 4 digits only (e.g., `+2******1234`) |
| **PII Protection** | `.gitignore` | Contacts CSV, participant state, audio, and logs excluded from git |
| **Route Protection** | `@app.before_request` | All `/admin` routes require session or admin token |
| **Webhook Passthrough** | Allowlist | Twilio webhook paths bypass auth |
| **Audit Logging** | JSONL | Every login/logout logged with IP, user-agent, timestamps |
| **Atomic Writes** | `os.replace()` | Prevents corrupt state files on crash |

---

## 8. Survey Question Engine

### 8.1 Question File Format

```
TYPE|Question Text|Option1|Option2|Option3...
```

### 8.2 Supported Question Types

| Type | Format | Input Method | Response Storage | Example |
|------|--------|-------------|-----------------|---------|
| **INFO** | `INFO\|text` | None | Not stored | `INFO\|Maswali sehemu ya kwanza` |
| **OPEN** | `OPEN\|text` | Speech (`<Gather input="speech">`) | Raw speech text | `OPEN\|Tafadhali sema jina lako` |
| **MCQ** | `MCQ\|text\|opt1\|opt2\|opt3` | DTMF keypad | Digit (1–9) | `MCQ\|Nani..?\|Marafiki\|Mume\|Watoto` |
| **MCQO** | `MCQO\|text\|opt1\|opt2\|Nyingine` | DTMF + optional speech | Digit (1–9) | `MCQO\|Kupanga..?\|Ndiyo\|Hapana\|Nyingine` |

### 8.3 IVR Question Flow

```
  Call Answered (inbound or outbound)
       |
       v
  /voice: Start Full-Call Recording (30 min max), tag direction
       |
       v
  /start: Play Q[0] + Q[1] (INFO intros)
       |
       v
  /start: Play Q[2] (First real question) with <Gather>
       |
       v
  +--- Question Type? ---+------------------+------------------+
  |                       |                  |                  |
  INFO                   OPEN               MCQ               MCQO
  |                       |                  |                  |
  Play text              Play text          Play text          Play text
  Pause 1s               Gather speech      + options          + options
  Redirect next          timeout=6s         Gather 1 digit     Gather 1 digit
                          |                  |                  |
                         Store              Store           Digit == Other?
                         SpeechResult       digit            |          |
                         mark_engaged()     mark_engaged()  No         Yes
                          |                  |               |          |
                          |                  |           Store      "Umechagua
                          |                  |           digit      nyingine..."
                          |                  |               |   Gather speech 4s
                          |                  |               |          |
  +---+------------------++------------------+--------+------+----------+
      |
      v
  Advance to Q[n+1]
      |
  More questions? Yes -> [loop]
                  No  -> "Kwaheri" + Hangup
```

### 8.4 TTS Prompt Generation

- **Voice:** `sw-KE-ZuriNeural` (Swahili) / `en-US-JennyNeural` (English)
- **Rate:** `-15%` prosody for clearer, slower delivery
- **Caching:** SHA1 hash of `voice|format|text` → disk-cached MP3 in `data/ivr_audio/`
- **Serving:** Public URL via `/ivr-audio/{hash}.mp3`, referenced in TwiML `<Play>` tags
- **SSML:** Full XML with entity escaping for special characters

### 8.5 MCQ Option Verbalization

```
"finya 1 kwa Ndiyo. finya 2 kwa Hapana. finya 3 kwa Nyingine."
```
("press 1 for Yes. press 2 for No. press 3 for Other.")

---

## 9. Configuration Reference

### 9.1 Environment Variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TWILIO_ACCOUNT_SID` | Yes | — | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Yes | — | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Yes | — | Twilio phone number (E.164) |
| `PUBLIC_BASE_URL` | Yes | — | Public HTTPS URL for webhooks |
| `ADMIN_TOKEN` | No | `""` | Optional token for admin access without login |
| `AZURE_SPEECH_KEY` | Yes | — | Azure Cognitive Services subscription key |
| `AZURE_SPEECH_REGION` | Yes | — | Azure region (e.g., `eastus`) |
| `AZURE_TTS_VOICE_SW` | No | `sw-KE-ZuriNeural` | Swahili TTS voice |
| `AZURE_TTS_VOICE_EN` | No | `en-US-JennyNeural` | English TTS voice |
| `AZURE_TTS_FORMAT` | No | `audio-16khz-128kbitrate-mono-mp3` | Audio format |
| `MAX_CALLS_PER_TICK` | No | `3` | Max outbound calls per scheduler tick |
| `CALL_SPACING_SEC` | No | `0.8` | Delay between outbound calls |
| `FLASK_SECRET_KEY` | No | `CHANGE_ME_NOW` | Flask session signing key |
| `AUTO_START_NGROK` | No | `1` | Auto-start ngrok on launch |
| `AUTH_MAX_FAILS` | No | `7` | Failed attempts before lockout |
| `AUTH_LOCK_SECONDS` | No | `900` | Lockout duration (15 minutes) |
| `AUTH_WINDOW_SECONDS` | No | `600` | Failure tracking window (10 minutes) |

### 9.2 Configuration File (`config.yaml`)

```yaml
twilio:
  account_sid: ""              # Overridden by .env
  auth_token: ""
  from_number: ""
  public_base_url: ""

ivr:
  questions_file: "data/questions.txt"
  gather_timeout_sec: 6
  speech_timeout: "auto"
  speech_language: "sw-KE"
  recording_max_seconds: 1800  # 30 minutes

audio_processing:
  enabled: true
  backend: "deepfilternet"
  processed_dir: "data/audio_processed"
  temp_dir: "data/audio_processed/tmp"
  output_sample_rate: 16000    # Whisper expects 16kHz
  model_sample_rate: 48000     # DeepFilterNet expects 48kHz
  channel_mode: "mixdown"      # "mixdown" or "channel"
  caller_channel: 0
  keep_intermediate_files: false

auth:
  users:
    username:
      password_hash: "pbkdf2:sha256:..."
```

### 9.3 System Constants

| Constant | Value | File | Description |
|----------|-------|------|-------------|
| `MAX_ATTEMPTS` | `3` | `state.py` | Maximum call attempts per participant |
| `RETRY_GAP` | `1 hour` | `state.py` | Minimum time between retries |
| `RECORDING_MAX_SEC` | `1800` | `twilio_handler.py` | Max recording length |
| `GATHER_TIMEOUT` | `6s` | `config.yaml` | DTMF/speech input timeout |
| `SCHEDULER_INTERVAL` | `15s` | `twilio_handler.py` | Scheduler polling interval |
| `WORKER_POLL` | `5s` | `background_worker.py` | Worker polling interval |
| `MAX_CHARS` | `3000` | `translate.py` | Max characters per translation chunk |
| `SCHEDULER_TIMEOUT_SEC` | `45s` | `runtime_status.py` | Scheduler heartbeat timeout |
| `WORKER_TIMEOUT_SEC` | `20s` | `runtime_status.py` | Worker heartbeat timeout |

---

## 10. Admin Dashboard

### 10.1 UI Layout

```
+-----------------------------------------------------------------------+
| AudioSurvey AI — Admin                        [RUNNING] [PAUSED]      |
| NYC time: 2026-04-05 14:32:15 EDT     Logged in as: krishnanand       |
|                                                           [Sign out]  |
+-----------------------------------------------------------------------+
| [Dial Now] [Start] [Stop] [Refresh] [Export Excel] [English] [Reset] |
+-----------------------------------------------------------------------+
| TECH INFO                                                             |
| Scheduler: Running (3s ago) | Worker: Running (1s ago) | Load: normal |
+-----------------------------------------------------------------------+
| +-----------+ +-----------+ +-----------+ +-----------+               |
| |    42     | |    10     | |     5     | |    25     |               |
| |   Total   | |  Pending  | |In Progress| | Completed |               |
| +-----------+ +-----------+ +-----------+ +-----------+               |
+-----------------------------------------------------------------------+
| Upload Contacts [CSV] | Questions Editor [Save] | Conference Call [Go]|
+-----------------------------------------------------------------------+
| Participants                                                          |
| +------+----------+----------+----+----------+------+--------+-----+ |
| | ID   | Phone    | Status   |Att.| Engaged  |Dir.  |Sched.  |Ctrl | |
| +------+----------+----------+----+----------+------+--------+-----+ |
| | P001 | +2****34 | Completed| 1  | Engaged  |In    |04-05   |     | |
| | P002 | +2****56 | Pending  | 0  | Not eng. |Out   |        |[Set]| |
| | P003 | +2****78 | InProg.  | 1  | Engaged  |In    |        |[End]| |
| +------+----------+----------+----+----------+------+--------+-----+ |
+-----------------------------------------------------------------------+
| [End All Calls]                                                       |
+-----------------------------------------------------------------------+
```

### 10.2 New Dashboard Features (v1.2.0)

| Feature | Description |
|---------|-------------|
| **Live Tech Info Panel** | Shows Scheduler status, Worker status, and system load level (quiet/normal/busy) — updated every poll cycle |
| **Call Direction Column** | Shows `Incoming` or `Outgoing` badge per participant based on call direction |
| **End Call Button** | Per-participant button (visible when call is `in_progress`) to immediately terminate that call via Twilio API |
| **End All Calls Button** | Global button to terminate all currently in-progress calls at once |
| **Refreshing Overlay** | Visual overlay during state reset operations to prevent user interaction during reset |
| **Redesigned Login Page** | Stronger branding, animated gradient, "Welcome" header, improved UX |
| **Runtime Status API** | `/admin/live_state` now includes `runtime` object with scheduler and worker heartbeat info |

### 10.3 Live Polling Architecture

```
  BROWSER (JS — every 1 second)      FLASK SERVER         participants.json
       |                                   |                     |
       |-- Guard checks:                  |                     |
       |   Skip if Flatpickr open         |                     |
       |   Skip if input dirty            |                     |
       |   Skip if poll in flight         |                     |
       |                                   |                     |
       |-- GET /admin/live_state -------->|                     |
       |                                   |-- load_participants |
       |                                   |-- get_runtime_snapshot()
       |<-- {total, counts,                |                     |
       |     participants, runtime}        |                     |
       |                                   |                     |
       |-- Update KPI cards               |                     |
       |-- Re-render table rows           |                     |
       |-- Update Tech Info panel         |                     |
       |-- Re-initialize Flatpickr        |                     |
```

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
       |    +===[Every 15 seconds]=====+                 |
       |    | mark_scheduler_heartbeat()|                |
       |    | load_participants()       |                |
       |    | Filter can_call()         |                |
       |    | client.calls.create()     |                |
       |    | mark_call_started()       |                |
       |    | save_participants()       |                |
       |    +===========================+                |
       |                                                 |
       |                    +===[Every 5 seconds]========+
       |                    | mark_worker_heartbeat()    |
       |                    | load_participants()        |
       |                    | Find processing_status     |
       |                    |   = "pending"              |
       |                    | Run ML pipeline            |
       |                    | mark_completed()           |
       |                    | save_participants()        |
       |                    +============================+
```

### 11.2 Worker Pipeline Stages

| Stage | Progress | Typical Duration | Description |
|-------|----------|-----------------|-------------|
| 1. Prepare | 10–25% | ~5s | FFmpeg: extract channel, resample to 48kHz mono PCM16 |
| 2. Denoise | 25–60% | ~30–90s | DeepFilterNet: neural noise removal (PyTorch) |
| 3. Resample | 60–75% | ~3s | FFmpeg: downsample to 16kHz for Whisper |
| 4. Transcribe | 75–85% | ~60–180s | Whisper large-v3: Swahili STT |
| 5. Translate | 85–93% | ~5–20s | Google Translate: chunked sw→en with retries |
| 6. English TTS | 93–97% | ~5–10s | gTTS: English audio synthesis |
| 7. Complete | 100% | — | Mark completed, save outputs to state |

### 11.3 Runtime Status Module (`runtime_status.py`)

Added in v1.2.0. Tracks heartbeats from both background threads and provides health status for the dashboard.

```python
# Statuses returned by get_runtime_snapshot():
# "not_started"  -> Thread hasn't started yet
# "starting"     -> Thread started but no heartbeat yet
# "running"      -> Last heartbeat within timeout window
# "paused"       -> Scheduler is paused (admin toggled)
# "down"         -> No heartbeat received within timeout
```

---

## 12. Inbound Call Handling

### 12.1 Overview (v1.2.0)

Inbound calls arrive when a participant dials the Twilio phone number directly. The system routes them through the exact same IVR survey and ML processing flow as outbound calls.

### 12.2 Inbound Participant Matching

```python
@app.route("/voice", methods=["POST"])
def voice():
    call_sid = request.values.get("CallSid")
    direction = request.values.get("Direction", "")  # "inbound" or "outbound-api"
    caller_number = request.values.get("From", "")   # E.164 phone number

    state = load_participants()
    pid, p = find_participant_by_callsid(state, call_sid)

    if not pid and direction == "inbound" and caller_number:
        # Try to match by phone number
        for existing_pid, existing_p in state.items():
            if existing_p.get("phone_e164") == caller_number:
                pid = existing_pid
                p = existing_p
                break

        if not pid:
            # Auto-create a new participant from the inbound number
            pid = f"inbound_{caller_number.replace('+', '').replace(' ', '_')}"
            upsert_participant(state, pid, caller_number)
            p = state[pid]

    # Tag direction on the participant record
    if pid:
        state[pid]["direction"] = direction
        mark_call_started(state, pid, call_sid)
        save_participants(state)
```

### 12.3 Call Controls (v1.2.0)

**End Individual Call:**
```python
@app.route("/admin/end_call", methods=["POST"])
def end_call():
    call_sid = request.form.get("call_sid")
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.calls(call_sid).update(status="completed")
```

**End All Active Calls:**
```python
@app.route("/admin/end_all_calls", methods=["POST"])
def end_all_calls():
    state = load_participants()
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    for pid, p in state.items():
        if p.get("status") == "in_progress" and p.get("last_call_sid"):
            client.calls(p["last_call_sid"]).update(status="completed")
```

---

## 13. Error Handling & Resilience

### 13.1 Fault Tolerance Matrix

| Component | Failure Mode | Handling Strategy |
|-----------|-------------|-------------------|
| **Twilio Call** | No answer / Busy | Mark `pending`, retry after 1h (up to 3 attempts) |
| **Twilio Call** | Failed / Canceled | Mark `failed` if max attempts reached |
| **Azure TTS** | API error | RuntimeError raised; corrupted audio not served |
| **Azure TTS** | Duplicate request | Disk cache by SHA1 hash prevents re-synthesis |
| **Whisper** | Hallucination drift | `condition_on_previous_text=False`, `temperature=0.0` |
| **Google Translate** | API error | 3 retries with 1.5s backoff; failed chunks marked `[TRANSLATION_FAILED_CHUNK]` |
| **Google Translate** | Returns `None` | Explicit `None` check; RuntimeError raised |
| **DeepFilterNet** | Processing error | Graceful fallback to unprocessed audio |
| **Recording Download** | HTTP error | Logged; returns 200 (Twilio won't retry webhook) |
| **State File** | Corrupt JSON | Renamed to `.corrupt`, returns empty state |
| **State File** | Concurrent access | `threading.RLock()` + atomic write (`.tmp` then `os.replace`) |
| **Scheduler** | Exception in tick | Caught and logged; loop continues |
| **Worker** | Exception in pipeline | Caught; `processing_status="failed"`; loop continues |
| **Auth State** | Missing file | Returns safe defaults `{"fails": {}, "locks": {}}` |
| **Inbound Call** | Unknown caller | Auto-creates participant record from phone number |
| **End Call API** | Call already ended | Twilio returns 200; exception caught and logged |

### 13.2 Retry Policy

```
  Call Placed (attempt N of 3)
       |
       +-- completed + engaged ---------> Status: completed
       |                                   Pipeline: triggered
       |
       +-- completed + NOT engaged -----> Status: pending
       |                                   (retry in 1h if < 3 attempts)
       |
       +-- no-answer / busy / failed / canceled
                                       |
                                  attempts >= 3?
                                       |          |
                                      Yes        No
                                       |          |
                                  Status:     Status: pending
                                  failed      (retry in 1h)
```

---

## 14. Logging & Observability

### 14.1 Logging Architecture

| Log Type | Format | Location | Purpose |
|----------|--------|----------|---------|
| **Application Log** | Colored console (colorlog) | stdout | Real-time operational visibility |
| **Auth Event Log** | JSONL | `data/auth_log.jsonl` | Security audit trail |
| **Call Log** | CSV | `data/state/call_log.csv` | Call history, recording tracking, direction |
| **Worker Progress** | Terminal progress bar | stdout | ML pipeline progress |
| **Runtime Status** | In-memory heartbeats | `runtime_status.py` | Scheduler/worker liveness |

### 14.2 Console Log Format

```
[NYC 2026-04-05T14:32:15-04:00 | UTC 2026-04-05T18:32:15Z] PROMPT SENT | CallSid=CA123 | Participant=P001 | q3_mcq | Text="..."
[BackgroundWorker] participant=P001 | [################----]  80% | Removing background noise
[Scheduler] 2026-04-05 14:32:30 EDT Calling P001 -> +254... | CallSid=CA123
```

### 14.3 Auth Event Log Format

```jsonl
{"event":"login","user":"krishnanand","ip":"127.0.0.1","login_utc":"2026-04-05T18:32:15Z","login_local":"2026-04-05 14:32:15 EDT","user_agent":"Mozilla/5.0..."}
{"event":"logout","user":"krishnanand","session_duration_sec":13365}
```

### 14.4 Silenced Libraries

`httpx`, `httpcore`, `httpcore.connection`, `httpcore.http2`, `hpack`, `h2`, `gtts`, `gtts.tts`, `googletrans`, `urllib3`, `torio`, `torchaudio`

---

## 15. Deployment Guide

### 15.1 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| pip | — | Package management |
| ngrok | 3.x | HTTPS tunneling |
| FFmpeg | 4.x+ | Audio processing |
| Twilio Account | — | Voice API |
| Azure Account | — | Cognitive Services TTS |

### 15.2 Local Development Setup

```bash
# 1. Clone and enter the repository
git clone https://github.com/krishnanand20/audiosurvey_ai.git
cd audiosurvey_ai

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Configure your credentials
cp .env.example .env
# Edit .env with your Twilio + Azure keys

# 5. Launch (auto-starts ngrok + Flask + opens admin in browser)
python3 run_app.py
```

### 15.3 Startup Sequence

```
  python3 run_app.py
       |
       +-- Check AUTO_START_NGROK env
       +-- Check if ngrok already running (localhost:4040)
       |
       +-- [No existing tunnel] Start ngrok http 5050
       +-- Poll /api/tunnels until HTTPS URL appears (20 retries)
       +-- Set PUBLIC_BASE_URL env var
       |
       +-- subprocess: python3 -m app.twilio_handler serve
           |
           +-- load_dotenv() + load_config()
           +-- Validate Twilio env vars
           +-- Load Whisper model large-v3 (cached globally)
           +-- init Azure TTS SDK
           +-- start_background_services()
           |   +-- Scheduler thread (daemon, 15s loop)
           |   +-- Worker thread (daemon, 5s poll)
           |
           +-- app.run(host="0.0.0.0", port=5050)
       |
       +-- Wait 1.5s
       +-- webbrowser.open("http://127.0.0.1:5050/admin")
```

### 15.4 macOS DMG Distribution

```bash
cd packaging/macos_dmg
./build_macos_dmg.sh
# Output: output/AudioSurvey-AI.dmg
```

**Build steps:** Swift icon generation → `.iconset` → `.icns` → `.app` bundle with launcher script → DMG

---

## 16. Directory Structure

```
audiosurvey_ai/
|
|-- .env                          # Environment variables (secrets — gitignored)
|-- .gitignore                    # Git exclusion rules
|-- config.yaml                   # Application configuration
|-- main.py                       # Batch processing entry point
|-- run_app.py                    # Application launcher
|-- requirements.txt              # Python dependencies (146 packages)
|-- README.md                     # Quick-start
|-- DOCUMENTATION.md              # This file
|-- STUDY_GUIDE.md                # Presentation study guide
|
|-- app/
|   |-- twilio_handler.py         # Flask app, IVR routes, inbound handling, auth (~1,780 lines)
|   |-- dashboard.py              # Admin dashboard UI + routes (~1,280 lines)
|   |-- runtime_status.py         # Background service health tracking (NEW v1.2.0)
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
|-- data/
|   |-- questions.txt             # Survey questions (pipe-delimited)
|   |-- state/
|   |   |-- participants.json     # All participant records, responses, status
|   |   |-- call_log.csv          # Call history with direction field
|   |   |-- settings.json         # System settings (paused flag)
|   |-- audio/                    # Raw call recordings (.wav)
|   |-- audio_processed/          # Denoised recordings (.wav)
|   |-- transcripts/              # Whisper transcriptions (.txt, Kiswahili)
|   |-- translations/             # English translations (.txt)
|   |-- english_audio/            # English TTS audio (.mp3)
|   |-- ivr_audio/                # Cached IVR prompts (.mp3, hash-named)
|   |-- results/
|       |-- ivr_responses.xlsx    # MCQ/MCQO responses (original)
|       |-- ivr_responses_english.xlsx # MCQ/MCQO responses (English)
|
|-- packaging/
    |-- macos_icon_generator.swift
    |-- macos_dmg/
        |-- build_macos_dmg.sh
        |-- output/AudioSurvey-AI.dmg
```

---

## 17. Dependency Matrix

### 17.1 Core Dependencies

| Package | Version | Purpose | Critical? |
|---------|---------|---------|-----------|
| `Flask` | 3.1.2 | Web framework | Yes |
| `twilio` | 9.10.0 | Telephony API (calls, TwiML, webhooks) | Yes |
| `openai-whisper` | 20240930 | Post-call speech-to-text (large-v3) | Yes |
| `azure-cognitiveservices-speech` | 1.48.1 | Neural TTS for IVR prompts | Yes |
| `googletrans` | 4.0.0rc1 | Kiswahili → English translation | Yes |
| `gTTS` | 2.5.4 | English audio generation | Yes |
| `deepfilternet` | 0.5.6 | Background noise removal | Medium |
| `torch` | 2.8.0 | ML framework (Whisper + DeepFilterNet) | Yes |
| `torchaudio` | 2.8.0 | Audio tensor operations | Yes |

### 17.2 Data & Export

| Package | Version | Purpose |
|---------|---------|---------|
| `pandas` | 2.3.3 | DataFrame operations for Excel export |
| `openpyxl` | 3.1.5 | Excel (.xlsx) file writing |
| `numpy` | 1.26.4 | Audio data numerical operations |
| `pydub` | 0.25.1 | Audio manipulation |

### 17.3 Infrastructure

| Package | Version | Purpose |
|---------|---------|---------|
| `python-dotenv` | 1.2.1 | `.env` file loading |
| `PyYAML` | 6.0.3 | `config.yaml` parsing |
| `gunicorn` | 23.0.0 | Production WSGI server |
| `Werkzeug` | 3.1.4 | Password hashing, HTTP utilities |
| `colorlog` | 6.10.1 | Colored console logging |
| `requests` | 2.32.5 | HTTP client (recording download) |
| `Jinja2` | 3.1.6 | Template rendering |

### 17.4 External Services

| Service | Provider | Purpose | Pricing |
|---------|----------|---------|---------|
| **Voice API** | Twilio | Outbound/inbound calls, recording, webhooks | Per-minute |
| **Speech TTS** | Azure Cognitive Services | Neural TTS prompts (Swahili + English) | Per-character |
| **Translation** | Google Translate (googletrans) | Kiswahili → English | Free (scraping) |
| **Text-to-Speech** | Google TTS (gTTS) | English audio output | Free |
| **Tunneling** | ngrok | HTTPS tunnel for Twilio webhooks | Free tier |

---

## 18. Glossary

| Term | Definition |
|------|-----------|
| **IVR** | Interactive Voice Response — automated phone menu system |
| **DTMF** | Dual-Tone Multi-Frequency — phone keypad tones (pressing 1–9, *, #) |
| **TwiML** | Twilio Markup Language — XML instructions for call scripting |
| **TTS** | Text-to-Speech — converting text to spoken audio |
| **STT** | Speech-to-Text — converting spoken audio to text |
| **SSML** | Speech Synthesis Markup Language — XML for controlling TTS prosody and voice |
| **E.164** | International phone number format (e.g., `+254700000000`) |
| **CallSid** | Unique Twilio identifier for a phone call |
| **Direction** | Call direction: `inbound` (participant called us) or `outbound-api` (we called them) |
| **DeepFilterNet** | PyTorch neural network for real-time speech enhancement and noise removal |
| **Whisper** | OpenAI's multilingual speech recognition model (large-v3 used here) |
| **MCQ** | Multiple Choice Question — DTMF keypad input |
| **MCQO** | Multiple Choice with Other — DTMF + optional speech for "Other" option |
| **OPEN** | Open-ended question — free speech input |
| **INFO** | Informational prompt — no response collected |
| **Engaged** | Participant produced detectable real speech during the call |
| **Pipeline** | The 4-stage ML chain: DeepFilterNet → Whisper → Google Translate → gTTS |
| **Heartbeat** | Periodic signal emitted by background threads to indicate they are alive |
| **Atomic Write** | Write to temp file then `os.replace()` — prevents partial/corrupted file writes |
| **RLock** | Reentrant Lock — a thread lock the same thread can acquire multiple times |
| **Daemon Thread** | Background thread that automatically exits when the main process ends |
| **ngrok** | Tunneling service that exposes localhost to the internet over HTTPS |
| **Kiswahili / sw** | Swahili language (ISO 639-1: `sw`; BCP 47 locale: `sw-KE`) |
| **PBKDF2** | Password-Based Key Derivation Function 2 — slow hashing for password storage |
| **PII** | Personally Identifiable Information (phone numbers, names) — kept gitignored |
| **Flatpickr** | JavaScript date/time picker library used in the admin dashboard |

<p align="center"><em>End of Document</em> &nbsp;|&nbsp; <code>AudioSurvey AI v1.2.0</code> &nbsp;|&nbsp; <code>April 6, 2026</code> &nbsp;|&nbsp; <code>Confidential — Restricted Distribution</code></p>
