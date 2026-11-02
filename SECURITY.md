# Security Policy & Architecture Transparency

Cromak Technology is committed to maintaining high standards of software security, privacy, and user data autonomy. As an accessible, local-first desktop application, **Cromak Bridge Vox** adheres to a strict zero-telemetry policy and direct provider integration.

---

## 1. Supported Versions

Security updates and patches are actively provided for the following versions:

| Version | Supported | Status |
| :--- | :---: | :--- |
| **1.3.x (Matrix Core)** | ✅ | Current stable release with active security updates |
| < 1.3.0 | ❌ | Deprecated. Please update to 1.3.5 or newer |

---

## 2. Reporting a Vulnerability

We take all security vulnerabilities seriously and appreciate responsible disclosure.

- **Do NOT open public GitHub Issues or Discussions** to report sensitive security vulnerabilities or zero-day exploits.
- **Reporting Channel:** Please send an email directly to our core security team at:
  **`cromaksupport@gmail.com`**
- **Include in your report:**
  - Description of the vulnerability and its potential impact.
  - Clear steps to reproduce (proof of concept, payload, or affected code path).
  - Version of Cromak Bridge Vox and Windows operating system version tested.
- **Response Timeline:**
  - You will receive an acknowledgment within **48 to 72 hours**.
  - A technical triage will follow, providing status updates and expected remediation timelines.
  - We ask that you maintain mutual confidentiality until an official fix is released.

---

## 3. Architecture Transparency: Local-First vs. External AI Providers

Cromak Bridge Vox does **not** route your traffic through proprietary proxy servers or Cromak backend relays. All communication adheres strictly to the following boundaries:

```
┌────────────────────────────────────────────────────────┐
│               LOCAL HOST (Your Computer)               │
│                                                        │
│  [ UI / Accessibility Layer ]                          │
│   ├── pywebview (Microsoft Edge WebView2)              │
│   ├── NVDA / Screen Reader ARIA Live Region Engine     │
│   └── 100% Offline Multi-language Packs (web/locale)   │
│                                                        │
│  [ Local Core & Storage ]                              │
│   ├── SQLite Database (%APPDATA%/.../bridge_database)  │
│   ├── Machine-Encrypted Config (%APPDATA%/.../config)  │
│   ├── Local Hotkey Hook (Alt+Space, F1-F11)            │
│   ├── Local FFmpeg Binary (plugins/ffmpeg/)            │
│   └── Auto-Coder (Local CLI & Script Execution)        │
└──────────────────────────┬─────────────────────────────┘
                           │ Direct TLS Outbound Calls (BYOK)
                           ▼
┌────────────────────────────────────────────────────────┐
│           THIRD-PARTY AI CLOUD PROVIDERS               │
│  • Groq Cloud API (https://api.groq.com)               │
│  • Google Gemini API (https://generativelanguage...)   │
│  • OpenAI API (https://api.openai.com)                 │
│  • Anthropic Claude API (https://api.anthropic.com)    │
│  • Alibaba Qwen API (DashScope)                        │
└────────────────────────────────────────────────────────┘
```

### Strictly Offline / Local Processing
The following tasks are handled 100% locally on your machine without internet transmission:
- **System Commands & Auto-Coder Execution:** Local shell scripts (`cmd.exe`, `powershell.exe`, Python interpreter) run directly within your local Windows user session.
- **Global Hotkeys & Accessibility:** Native Windows input hooks (`Alt+Space`, `Ctrl+Space`, function keys) run in-process using Win32 API.
- **Local Persistence & Reminders:** Chat history, user profiles, and calendar alarms are stored in a local SQLite database (`bridge_database.db`) located in `%APPDATA%\Cromak Technology\Bridge Vox\`.
- **Audio Capture & Conversion:** Microphone input is captured locally using `pyaudio`/`sounddevice` and transformed via the local FFmpeg binary (`plugins/ffmpeg/ffmpeg.exe`).
- **Screen Reading:** ARIA live regions and DOM focus events communicate with assistive technologies (NVDA, JAWS, Windows Narrator) entirely within your local browser runtime.
- **Language Packs:** The 11 supported languages are stored in static JSON files in `web/locale/` and loaded locally into memory.

### External AI Providers (BYOK - Bring Your Own Key)
Cromak Technology does **not** act as an intermediary. When you send a prompt:
- Direct HTTPS/TLS connections are established from your computer to the official endpoints of your chosen provider:
  - **Groq Cloud:** `https://api.groq.com/openai/v1`
  - **Google Gemini:** `https://generativelanguage.googleapis.com`
  - **OpenAI:** `https://api.openai.com/v1`
  - **Anthropic:** `https://api.anthropic.com/v1`
  - **Alibaba Qwen:** `https://dashscope.aliyuncs.com`
- Only the specific prompt text and files you explicitly attach (images, PDFs, documents, audio clips) are sent to the provider. Data handling is governed solely by the privacy policy of the selected provider.

---

## 4. Permissions, Credentials, and Data Governance

### Windows User Privileges
- **Standard User Execution:** Cromak Bridge Vox runs in standard user space (`asInvoker`). It does **not** require administrator elevation to operate normally.
- **Administrative Privileges:** Administrator rights are only requested during installation (to write to `Program Files`) or when the user explicitly triggers an Auto-Coder action requiring elevated system rights.

### Storage of API Keys & Credentials
- All API keys entered in the settings panel are stored locally in:
  `%APPDATA%\Cromak Technology\Bridge Vox\config.json`
- **Encryption at Rest:** Keys are encrypted at rest using machine-specific cryptographic identifiers (`hostname` + project-specific salt, hashed with SHA-256 and encrypted via XOR/Base64 or Fernet).
- Keys are never logged in plain text, never synchronized to cloud backups, and never transmitted to Cromak Technology.

### Voice & Microphone Recordings
- Microphone access occurs **only** when the user initiates voice recording (e.g., holding `F2` or activating Walkie-Talkie mode).
- Voice recordings are written to temporary WAV files or in-memory buffers for local playback or speech-to-text processing.
- Cromak Bridge Vox does **not** maintain background audio surveillance or persistent voice recording logs. Temporary audio files are discarded after processing.

### Screenshots & Screen Vision
- Screen captures are triggered **strictly** upon user command (e.g., asking the assistant to inspect the current screen or clicking the vision capture button).
- Screenshots are saved temporarily to disk, encoded for multimodal submission to the selected AI provider, and removed.
- No automated, continuous, or background screen recording occurs.

### Auto-Coder Agent Safety
- When **Agent Mode** is activated, the assistant can read and write files on your local file system and execute shell commands.
- **User Responsibility:** Cromak Bridge Vox is designed for maximum developer power and autonomy. You are responsible for inspecting commands before authorization. We recommend not running untrusted third-party prompts with Agent Mode enabled.
