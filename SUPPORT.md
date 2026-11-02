# Getting Support for Cromak Bridge Vox

Welcome to the **Cromak Bridge Vox** support page! We are here to help you get the most out of your accessible AI desktop assistant.

---

## 1. Official Support Channels

Please use the appropriate channel based on your need:

| Topic | Channel | Best For |
| :--- | :--- | :--- |
| **Bug Reports** | [GitHub Issues](https://github.com/CromakTechnology/cromak-bridge-vox/issues) | Software defects, crashes, unexpected behavior |
| **Accessibility Barriers** | [GitHub A11y Issues](https://github.com/CromakTechnology/cromak-bridge-vox/issues/new?template=accessibility_issue.yml) | Screen reader incompatibilities, focus traps, keyboard navigation issues |
| **Feature Suggestions** | [GitHub Feature Requests](https://github.com/CromakTechnology/cromak-bridge-vox/issues/new?template=feature_request.yml) | New models, workflow automations, UI enhancements |
| **Community Q&A** | [GitHub Discussions](https://github.com/CromakTechnology/cromak-bridge-vox/discussions) | Usage questions, prompt tips, workflow sharing |
| **Official Support & Inquiries** | `cromaksupport@gmail.com` | Institutional partnerships, sensitive questions, and direct support |
| **Official Website** | [cromaktechnology.github.io](https://cromaktechnology.github.io) | Official downloads, changelogs, documentation |

---

## 2. In-Tree Documentation

The repository includes detailed documentation inside the `docs/` folder:

- **`docs/README.txt`:** Quick start and architectural overview.
- **`docs/roteiro-testes.txt`:** Comprehensive manual testing guide, including keyboard shortcuts and accessibility verification steps.
- **`docs/PRIVACY.txt`:** Full data privacy policy and local data handling guidelines.
- **`docs/EULA.txt`:** End User License Agreement.
- **`docs/api-teste.txt`:** Guidelines for testing AI provider APIs (Groq, Gemini, OpenAI, Claude, Qwen).

---

## 3. Common Troubleshooting Steps

### 1. "Microsoft Edge WebView2 Runtime is missing"
- **Symptom:** The application fails to launch or displays an error dialog indicating that WebView2 is missing.
- **Cause:** Common in specialized Windows installations (Windows 10 LTSC, Windows Server, or Windows IoT editions).
- **Solution:** Download and install the free official [Microsoft Edge WebView2 Evergreen Bootstrapper](https://go.microsoft.com/fwlink/p/?LinkId=2124703). Standard Windows 10 and 11 editions already have this pre-installed.

### 2. "Microphone does not capture audio"
- **Symptom:** Holding `F2` produces silence or an audio error.
- **Cause:** Windows privacy settings blocking microphone access, or missing `ffmpeg.exe`.
- **Solution:**
  1. Open Windows Settings -> **Privacy & Security** -> **Microphone**, and ensure desktop apps have access.
  2. If running from source, ensure `ffmpeg.exe` and `ffprobe.exe` are present in `plugins/ffmpeg/` or installed in `PATH`.

### 3. "Global hotkey Alt+Space or F1-F11 not responding"
- **Symptom:** Pressing `Alt+Space` does not bring Bridge Vox to the foreground.
- **Cause:** Another active software (such as PowerToys Run or a custom gaming utility) has already registered the same hotkey combination.
- **Solution:** Use the secondary global hotkey: **`Ctrl+Space`**. Alternatively, click the notification tray icon or reopen Bridge Vox from the taskbar.

### 4. "API Key Error / Rate Limit Reached"
- **Symptom:** The assistant responds with a red error alert or a 401/429 status code.
- **Cause:** Invalid API key, expired trial balance, or provider rate limits.
- **Solution:** Open the settings menu (`⚙️`) or press `F10`, verify that your API key is correctly pasted, and confirm that your key has active credits in your provider console (e.g., [console.groq.com](https://console.groq.com/) or [aistudio.google.com](https://aistudio.google.com/)).

---

## 4. Need Further Help?

If none of the above resolves your issue, please open an issue on GitHub with your reproduction steps and logs, or reach out to **`cromaksupport@gmail.com`**.
