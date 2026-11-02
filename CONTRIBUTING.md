# Contributing to Cromak Bridge Vox

Thank you for your interest in contributing to **Cromak Bridge Vox**! Our mission is to build the world's most capable, fast, and accessible AI desktop assistant, with zero barriers for blind and low-vision users.

Whether you are fixing a bug, adding a new model provider, translating strings, or conducting assistive technology audits, your contributions make a direct impact.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). We maintain a respectful, welcoming, and radically inclusive environment for everyone.

---

## How Can You Contribute?

You can contribute in three main areas:

1. **Core Development:** Python backend (`main.py`, `core/`), frontend interface (`web/index.html`, `web/js/script.js`, `web/js/vox-mode.js`), and build automation.
2. **Localization & Translations (i18n):** Translating and refining language files in `web/locale/`.
3. **Accessibility Auditing (a11y):** Testing features with screen readers (NVDA, JAWS, Windows Narrator) and keyboard-only navigation.

---

## Development Environment Setup

### Prerequisites
- **Operating System:** Windows 10 or Windows 11 (64-bit).
- **Python:** Version 3.10 or higher (make sure `python` is added to your system `PATH`).
- **Microsoft Edge WebView2 Runtime:** Native on standard Windows 10/11; required for Windows 10 LTSC/IoT editions ([Download](https://go.microsoft.com/fwlink/p/?LinkId=2124703)).
- **FFmpeg:** Required for voice capture, audio decoding, and playback. Place `ffmpeg.exe` and `ffprobe.exe` into `plugins/ffmpeg/` or have them available on the system `PATH`.
- **Screen Reader (Recommended for testing):** [NVDA (NonVisual Desktop Access)](https://www.nvaccess.org/) is our primary testing benchmark (free and open source).

### Step-by-Step Setup

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/cromak-bridge-vox.git
cd cromak-bridge-vox

# 2. Create and activate an isolated virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install development dependencies
pip install -r requirements.txt

# 4. Verify FFmpeg binary location
# Place ffmpeg.exe inside plugins/ffmpeg/ if not globally installed

# 5. Launch the application in developer mode
python main.py
```

---

## Branching & Git Workflow

We use a standard GitHub feature branch workflow:

1. Always branch off the latest `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b <type>/<short-description>
   ```
2. Branch naming conventions:
   - `feat/<feature-name>`: New feature or capability
   - `fix/<bug-name>`: Bug fix
   - `a11y/<accessibility-improvement>`: Accessibility and screen reader improvements
   - `i18n/<language-code>`: Translation and localization updates
   - `docs/<doc-name>`: Documentation updates

---

## Commit Guidelines (Conventional Commits)

We enforce clear, standardized commit messages following [Conventional Commits](https://www.conventionalcommits.org/):

Format: `<type>(<scope>): <subject>`

### Allowed Types
- `feat`: A new user-facing feature or model capability
- `fix`: A bug fix
- `a11y`: Accessibility improvements (ARIA, keyboard navigation, NVDA focus)
- `i18n`: Translations or locale adjustments
- `docs`: Documentation changes
- `refactor`: Code refactoring without behavioral changes
- `chore`: Build script, dependencies, or repository housekeeping

### Examples
- `feat(groq): add support for llama-3.3-70b-versatile`
- `fix(tray): preserve notification icon on Windows Action Center`
- `a11y(exit): ensure NVDA priority announcement on F4 confirmation modal`
- `i18n(fr_FR): complete 161 translation keys for French locale`

---

## Localization & Internationalization (i18n)

Cromak Bridge Vox supports 11 native languages stored in `web/locale/`:

| Locale Code | Language | File |
| :---: | :--- | :--- |
| `pt_BR` | Português (Brasil) | `web/locale/pt_BR.json` |
| `en_US` | English (US) | `web/locale/en_US.json` |
| `es_ES` | Español | `web/locale/es_ES.json` |
| `fr_FR` | Français | `web/locale/fr_FR.json` |
| `de_DE` | Deutsch | `web/locale/de_DE.json` |
| `it_IT` | Italiano | `web/locale/it_IT.json` |
| `zh_CN` | 中文 (简体) | `web/locale/zh_CN.json` |
| `ja_JP` | 日本語 | `web/locale/ja_JP.json` |
| `ru_RU` | Русский | `web/locale/ru_RU.json` |
| `hi_IN` | हिन्दी | `web/locale/hi_IN.json` |
| `ar_SA` | العربية | `web/locale/ar_SA.json` |

### Adding or Updating Translations:
1. Every locale file must contain the exact same set of translation keys (currently 161 keys).
2. Never remove existing keys.
3. Keep terminology natural and accessible for screen reader speech output.
4. Test that the language selector updates all UI elements in real time.

---

## Accessibility Quality Standards (Mandatory)

Every pull request impacting user interaction must adhere to our accessibility standards:

### 1. Keyboard-Only Navigation
- Every clickable button, link, input field, and modal must be reachable and operable using `Tab`, `Shift+Tab`, `Enter`, `Space`, or designated hotkeys.
- The visual focus indicator (`:focus-visible`) must be sharp and distinct at all times.
- **No focus traps:** The user must be able to navigate into and out of any component (e.g., closing modals with `Esc`).

### 2. Screen Reader Fluency (NVDA / Narrator / JAWS)
- **ARIA Live Regions:** Dynamic AI output must update via live regions (`aria-live="polite"`). Never flood the screen reader with every streaming token if it disrupts intelligibility.
- **Semantic HTML:** Use proper HTML tags (`<button>`, `<main>`, `<nav>`, `<input>`) before resorting to `<div>` with ARIA roles.
- **Labels & Descriptions:** Every icon button must have a clear `aria-label` or accessible text description.
- **NVDA Speech Viewer Testing:** Open the NVDA menu (`NVDA+N` -> Tools -> Speech Viewer) and verify that speech logs read cleanly without duplicated or chopped speech.

### 3. High Contrast & Visual Accessibility
- All colors must meet WCAG AAA contrast ratio standards.
- High Contrast / Vox Mode must maintain pure black backgrounds (`#000000`) and high-luminance elements without clutter.

---

## Submitting a Pull Request (PR)

1. Ensure your changes compile and run without errors:
   ```bash
   python -m py_compile main.py
   python main.py
   ```
2. Fill out the mandatory checklist in the [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).
3. If you changed UI elements, specify which screen reader and keyboard tests you performed.
4. Keep PRs focused on a single topic. Avoid bundling unrelated refactors with functional changes.
5. Our maintainers will review your PR and provide constructive feedback.
