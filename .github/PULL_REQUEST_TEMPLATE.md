## Summary of Changes

<!-- Please provide a clear and concise description of what this PR accomplishes. -->

---

## Type of Change

<!-- Mark the appropriate option with an [x]. -->

- [ ] 🐛 **Bug fix** (non-breaking change fixing an issue)
- [ ] ✨ **New feature** (non-breaking change adding functionality or new AI model)
- [ ] ♿ **Accessibility (a11y)** (improving screen reader, keyboard navigation, or contrast)
- [ ] 🌐 **Internationalization (i18n)** (new or updated language packs)
- [ ] 📝 **Documentation** (updates to README, docs, or guides)
- [ ] 🧹 **Refactor / Maintenance** (code cleanup, build scripts, dependency updates)

---

## Accessibility & Screen Reader Verification (MANDATORY)

> **Cromak Bridge Vox is an accessibility-first project.** Any regression in screen reader fluency or keyboard navigation will block the PR from being merged.

Please confirm the following tests were conducted:

- [ ] **Keyboard-Only Navigation:** I operated the new or modified UI entirely via keyboard (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Esc`, Hotkeys). No mouse interaction was required.
- [ ] **Focus Management:** Visual focus indicator remained clear at all times, focus was not lost, and there are no focus traps.
- [ ] **Screen Reader Verification:** Tested with at least one assistive technology:
  - [ ] NVDA (tested with Speech Viewer active)
  - [ ] Windows Narrator
  - [ ] JAWS
  - [ ] Other: _____________
- [ ] **ARIA Live Regions:** Dynamic updates and streaming responses announce cleanly without stuttering, repetition, or flooding the audio channel.
- [ ] **Accessibility Non-Regression Statement:** I confirm this change **does not break or degrade** existing accessibility workflows for blind and low-vision users.

---

## Technical Checklist

- [ ] My code compiles cleanly without syntax errors (`python -m py_compile main.py`).
- [ ] Tested locally on Windows 10 or Windows 11.
- [ ] No hardcoded secrets, API keys, or private tokens are included.
- [ ] If new UI strings were added, corresponding keys were added across all `web/locale/*.json` files.
- [ ] Existing functionality remains unaffected or tests have been updated.

---

## Screenshots or Screen Reader Logs (If applicable)

<!-- 
If this is a visual change, attach a screenshot.
If this is an accessibility change, paste the NVDA Speech Viewer log below.
-->
