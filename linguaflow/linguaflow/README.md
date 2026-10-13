# LinguaFlow - Translate Anywhere

A system-wide translator for the desktop. Select text in ANY app (Discord, WhatsApp Desktop,
Instagram in a browser, games in windowed mode...), press a hotkey, and see the translation
in a small overlay without leaving the app. Reply mode translates your answer back into the
sender's language and pastes it into the chat.

## Setup (Windows)
    pip install -r requirements.txt
    python linguaflow.py

## Hotkeys
- Ctrl+Alt+T : translate selected text (auto-detects the language)
- Ctrl+Alt+R : translate the reply in your clipboard into the sender's language and paste it
- Ctrl+Alt+Q : quit

## Settings
Edit settings.json: "target_language" (e.g. "en", "hi", "ja") and "overlay_seconds".

## Privacy
Text is sent to Google's translation service via deep-translator. Nothing is stored except a
local history.json (last 200 translations) on your machine.

## Roadmap
- OCR fallback for text that can't be selected (images, games)
- Android version (Kotlin: AccessibilityService + floating bubble + ML Kit offline translation)
- Offline engine, speech translation
