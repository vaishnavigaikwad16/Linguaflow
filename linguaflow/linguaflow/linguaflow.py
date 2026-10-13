"""
LinguaFlow - Translate Anywhere (desktop prototype)

How it works (works over Discord, WhatsApp Desktop, browsers, games in windowed mode, etc.):
  Ctrl+Alt+T  -> copies your current text selection, detects its language,
                 translates it to your target language and shows a small overlay.
  Ctrl+Alt+R  -> reply mode: translates the text currently in your clipboard
                 into the language of the last message you translated, and
                 pastes it into the focused chat box.
  Ctrl+Alt+Q  -> quit.

Run:  python linguaflow.py
"""

import json
import threading
import time
import tkinter as tk
from pathlib import Path

import keyboard          # global hotkeys
import pyperclip         # clipboard access
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # make language detection deterministic

CONFIG_PATH = Path(__file__).with_name("settings.json")
HISTORY_PATH = Path(__file__).with_name("history.json")
DEFAULTS = {"target_language": "en", "overlay_seconds": 8}


def load_config():
    if CONFIG_PATH.exists():
        try:
            return {**DEFAULTS, **json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


CONFIG = load_config()
last_source_lang = {"code": None}  # language of the last message we translated


# ---------- core logic ----------
def translate(text, target):
    """Detect language and translate. Returns (source_lang, translated_text)."""
    try:
        source = detect(text)
    except Exception:
        source = "auto"
    out = GoogleTranslator(source=source, target=target).translate(text)
    return source, out


def save_history(src_lang, target, original, translated):
    items = []
    if HISTORY_PATH.exists():
        try:
            items = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            items = []
    items.append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "from": src_lang, "to": target,
        "original": original, "translated": translated,
    })
    HISTORY_PATH.write_text(json.dumps(items[-200:], ensure_ascii=False, indent=2),
                            encoding="utf-8")


def grab_selection():
    """Copy the current selection via Ctrl+C and return it, restoring the clipboard."""
    previous = pyperclip.paste()
    pyperclip.copy("")
    keyboard.send("ctrl+c")
    time.sleep(0.15)
    text = pyperclip.paste().strip()
    if not text:
        pyperclip.copy(previous)
    return text


# ---------- overlay UI ----------
class Overlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.win = None

    def show(self, header, original, translated):
        self.root.after(0, self._show, header, original, translated)

    def _show(self, header, original, translated):
        if self.win is not None:
            self.win.destroy()
        w = tk.Toplevel(self.root)
        self.win = w
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.attributes("-alpha", 0.96)
        w.configure(bg="#1e1e2e")
        sw = w.winfo_screenwidth()
        w.geometry(f"420x190+{sw - 440}+60")

        tk.Label(w, text=header, bg="#1e1e2e", fg="#89b4fa",
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 0))
        tk.Label(w, text=original, bg="#1e1e2e", fg="#a6adc8", wraplength=390,
                 justify="left", anchor="w", font=("Segoe UI", 10)).pack(fill="x", padx=14, pady=(4, 6))
        tk.Label(w, text=translated, bg="#1e1e2e", fg="#cdd6f4", wraplength=390,
                 justify="left", anchor="w", font=("Segoe UI", 13, "bold")).pack(fill="x", padx=14)
        tk.Label(w, text="click to dismiss  |  copied to clipboard", bg="#1e1e2e",
                 fg="#6c7086", font=("Segoe UI", 8)).pack(side="bottom", pady=6)

        w.bind("<Button-1>", lambda e: w.destroy())
        w.after(int(CONFIG["overlay_seconds"] * 1000),
                lambda: w.winfo_exists() and w.destroy())

    def run(self):
        self.root.mainloop()


overlay = Overlay()


# ---------- hotkey handlers ----------
def on_translate():
    text = grab_selection()
    if not text:
        overlay.show("LinguaFlow", "", "Select some text first, then press Ctrl+Alt+T.")
        return
    try:
        src, out = translate(text, CONFIG["target_language"])
    except Exception as exc:  # network errors etc.
        overlay.show("LinguaFlow - error", text, f"Translation failed: {exc}")
        return
    last_source_lang["code"] = src
    pyperclip.copy(out)
    save_history(src, CONFIG["target_language"], text, out)
    overlay.show(f"{src.upper()}  ->  {CONFIG['target_language'].upper()}", text, out)


def on_reply():
    draft = pyperclip.paste().strip()
    target = last_source_lang["code"]
    if not draft or not target or target == "auto":
        overlay.show("LinguaFlow", "",
                     "Translate a message first (Ctrl+Alt+T), then copy your reply and press Ctrl+Alt+R.")
        return
    try:
        out = GoogleTranslator(source="auto", target=target).translate(draft)
    except Exception as exc:
        overlay.show("LinguaFlow - error", draft, f"Translation failed: {exc}")
        return
    pyperclip.copy(out)
    time.sleep(0.1)
    keyboard.send("ctrl+v")  # paste into the focused chat box
    save_history(CONFIG["target_language"], target, draft, out)
    overlay.show(f"REPLY  ->  {target.upper()}", draft, out)


def threaded(fn):
    return lambda: threading.Thread(target=fn, daemon=True).start()


def main():
    keyboard.add_hotkey("ctrl+alt+t", threaded(on_translate))
    keyboard.add_hotkey("ctrl+alt+r", threaded(on_reply))
    keyboard.add_hotkey("ctrl+alt+q", lambda: overlay.root.after(0, overlay.root.destroy))
    print("LinguaFlow running. Ctrl+Alt+T translate | Ctrl+Alt+R reply | Ctrl+Alt+Q quit")
    overlay.run()


if __name__ == "__main__":
    main()
