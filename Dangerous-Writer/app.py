"""
The Dangerous Writing App
─────────────────────────
Start typing. If you stop for more than 5 seconds, EVERYTHING is deleted.
Run with:  python dangerous_writer.py
Requires:  Python 3.x  (tkinter is included in the standard library)
"""

import tkinter as tk
from tkinter import font as tkfont
import time


# ── Constants ────────────────────────────────────────────────────────────────

LIMIT_MS      = 5000          # milliseconds before deletion
TICK_MS       = 50            # how often to refresh the timer (ms)
DANGER_AT     = 0.60          # fraction of time left where amber warning starts
CRITICAL_AT   = 0.30          # fraction of time left where red critical starts
SHAKE_AT      = 1500          # ms remaining when shaking starts

# Colour palette
BG            = "#0a0a0a"
TEXT_FG       = "#d4ccc0"
MUTED         = "#4a4540"
ACCENT_SAFE   = "#3a3028"
ACCENT_WARN   = "#b87020"
ACCENT_DANGER = "#c0281a"
OVERLAY_RED   = "#c0281a"
HEADER_FG     = "#8a7f70"
STAT_FG       = "#c8bfb0"
PLACEHOLDER   = "#2e2b27"
CARET         = "#e05540"


# ── Main Application ──────────────────────────────────────────────────────────

class DangerousWriterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("The Dangerous Writer")
        self.root.configure(bg=BG)
        self.root.geometry("820x620")
        self.root.minsize(600, 480)
        self.root.resizable(True, True)

        # State
        self.started      = False
        self.dead         = False
        self.last_type_ms = 0
        self.shake_job    = None
        self.tick_job     = None
        self._shake_dx    = 0

        self._build_ui()
        self._show_waiting()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=0, pady=0)

        tk.Label(
            header, text="THE DANGEROUS WRITER",
            bg=BG, fg=HEADER_FG,
            font=("Courier New", 11, "bold"),
            anchor="w", pady=10, padx=20,
        ).pack(side="left")

        self.status_var = tk.StringVar(value="Waiting for you to begin…")
        tk.Label(
            header, textvariable=self.status_var,
            bg=BG, fg=MUTED,
            font=("Courier New", 9),
            anchor="e", padx=20,
        ).pack(side="right")

        # ── Timer bar ─────────────────────────────────────────────────────────
        bar_frame = tk.Frame(self.root, bg="#111111", height=4)
        bar_frame.pack(fill="x")
        bar_frame.pack_propagate(False)

        self.bar_canvas = tk.Canvas(
            bar_frame, height=4, bg="#111111",
            highlightthickness=0,
        )
        self.bar_canvas.pack(fill="both", expand=True)
        self.bar_rect = self.bar_canvas.create_rectangle(
            0, 0, 0, 4, fill=ACCENT_SAFE, outline=""
        )

        # ── Stats row ─────────────────────────────────────────────────────────
        meta = tk.Frame(self.root, bg=BG, pady=6)
        meta.pack(fill="x", padx=20)

        self.words_var = tk.StringVar(value="0")
        self.chars_var = tk.StringVar(value="0")
        self.count_var = tk.StringVar(value="—")

        for val_var, label in (
            (self.words_var, "words"),
            (self.chars_var, "chars"),
        ):
            f = tk.Frame(meta, bg=BG)
            f.pack(side="left", padx=(0, 24))
            tk.Label(f, textvariable=val_var, bg=BG, fg=STAT_FG,
                     font=("Courier New", 20)).pack(side="left")
            tk.Label(f, text=f"  {label}", bg=BG, fg=MUTED,
                     font=("Courier New", 9)).pack(side="left", padx=(2, 0))

        # Countdown (right-aligned)
        cd_frame = tk.Frame(meta, bg=BG)
        cd_frame.pack(side="right")
        self.count_label = tk.Label(
            cd_frame, textvariable=self.count_var,
            bg=BG, fg=MUTED,
            font=("Courier New", 32),
        )
        self.count_label.pack(side="right")
        tk.Label(
            cd_frame, text="sec\nleft", bg=BG, fg=MUTED,
            font=("Courier New", 8), justify="right",
        ).pack(side="right", padx=(0, 6))

        # Separator
        tk.Frame(self.root, bg="#1a1a1a", height=1).pack(fill="x")

        # ── Text editor ───────────────────────────────────────────────────────
        editor_frame = tk.Frame(self.root, bg=BG)
        editor_frame.pack(fill="both", expand=True, padx=0)

        self.text = tk.Text(
            editor_frame,
            bg=BG, fg=TEXT_FG,
            insertbackground=CARET,
            font=("Courier New", 15),
            relief="flat",
            bd=0,
            padx=28, pady=24,
            wrap="word",
            undo=True,
            spacing1=4, spacing3=4,
            selectbackground="#2a2520",
            selectforeground=TEXT_FG,
        )
        self.text.pack(fill="both", expand=True)

        # Placeholder text
        self._placeholder_active = True
        self.text.insert("1.0", "Start typing. Don't you dare stop…")
        self.text.config(fg=PLACEHOLDER)
        self.text.bind("<FocusIn>",  self._clear_placeholder)
        self.text.bind("<FocusOut>", self._restore_placeholder)
        self.text.bind("<Key>",       self._on_key)

        # ── Footer ────────────────────────────────────────────────────────────
        tk.Frame(self.root, bg="#1a1a1a", height=1).pack(fill="x")
        footer = tk.Frame(self.root, bg=BG, pady=8)
        footer.pack(fill="x", padx=20)

        tk.Label(
            footer,
            text="Stop for 5 seconds → everything vanishes",
            bg=BG, fg="#2e2b27",
            font=("Courier New", 9),
        ).pack(side="left")

        tk.Button(
            footer, text="Start Over",
            bg=BG, fg=MUTED,
            activebackground="#1a1a1a", activeforeground=HEADER_FG,
            relief="flat", bd=1,
            font=("Courier New", 9),
            cursor="hand2",
            command=self.reset,
            padx=12, pady=4,
        ).pack(side="right")

        # ── Overlay (destruction screen) ──────────────────────────────────────
        self.overlay = tk.Frame(self.root, bg=BG)

        tk.Label(
            self.overlay,
            text="GONE.\nALL OF IT.",
            bg=BG, fg=OVERLAY_RED,
            font=("Courier New", 44, "bold"),
            justify="center",
        ).pack(pady=(80, 0))

        tk.Label(
            self.overlay,
            text="you stopped.  your words are ash.",
            bg=BG, fg=MUTED,
            font=("Courier New", 10),
        ).pack(pady=(16, 0))

        tk.Button(
            self.overlay,
            text="BEGIN AGAIN",
            bg=BG, fg=TEXT_FG,
            activebackground="#1a1a1a", activeforeground=OVERLAY_RED,
            relief="flat", bd=1,
            font=("Courier New", 11),
            cursor="hand2",
            command=self.reset,
            padx=20, pady=8,
        ).pack(pady=36)

    # ── Placeholder helpers ───────────────────────────────────────────────────

    def _clear_placeholder(self, _event=None):
        if self._placeholder_active:
            self.text.delete("1.0", "end")
            self.text.config(fg=TEXT_FG)
            self._placeholder_active = False

    def _restore_placeholder(self, _event=None):
        if not self.text.get("1.0", "end-1c").strip():
            self._placeholder_active = True
            self.text.insert("1.0", "Start typing. Don't you dare stop…")
            self.text.config(fg=PLACEHOLDER)

    # ── Input handling ────────────────────────────────────────────────────────

    def _on_key(self, event):
        if self.dead:
            return "break"          # block all input on dead state

        # Ignore pure modifier keys
        if event.keysym in ("Shift_L","Shift_R","Control_L","Control_R",
                             "Alt_L","Alt_R","Caps_Lock","Tab",
                             "Left","Right","Up","Down"):
            return

        self._clear_placeholder()
        self.last_type_ms = self._now()

        if not self.started:
            self.started = True
            self._tick()

        # Update stats after tkinter processes the keystroke
        self.root.after(1, self._update_stats)

    # ── Timer tick ────────────────────────────────────────────────────────────

    def _tick(self):
        if self.dead or not self.started:
            return

        elapsed   = self._now() - self.last_type_ms
        remaining = max(0, LIMIT_MS - elapsed)
        frac      = remaining / LIMIT_MS

        self._update_bar(frac)
        self._update_countdown(remaining)
        self._update_danger_colours(frac)

        if remaining <= SHAKE_AT and remaining > 0:
            self._do_shake()

        if remaining <= 0:
            self._obliterate()
            return

        self.tick_job = self.root.after(TICK_MS, self._tick)

    # ── Visual updates ────────────────────────────────────────────────────────

    def _update_bar(self, frac: float):
        self.bar_canvas.update_idletasks()
        w = self.bar_canvas.winfo_width()
        self.bar_canvas.coords(self.bar_rect, 0, 0, int(w * frac), 4)

    def _update_countdown(self, remaining_ms: int):
        secs = max(0, (remaining_ms + 999) // 1000)   # ceiling
        self.count_var.set(str(secs) if self.started else "—")

    def _update_danger_colours(self, frac: float):
        if frac > DANGER_AT:
            colour = ACCENT_SAFE
            fg     = MUTED
            status = "Writing…"
        elif frac > CRITICAL_AT:
            colour = ACCENT_WARN
            fg     = ACCENT_WARN
            status = "Keep going…"
        else:
            colour = ACCENT_DANGER
            fg     = ACCENT_DANGER
            status = "WRITE NOW"

        self.bar_canvas.itemconfig(self.bar_rect, fill=colour)
        self.count_label.config(fg=fg)
        self.words_var   # stat colour update
        self.status_var.set(status)

    def _update_stats(self):
        content = self.text.get("1.0", "end-1c")
        if self._placeholder_active:
            content = ""
        words = len(content.split()) if content.strip() else 0
        self.words_var.set(str(words))
        self.chars_var.set(str(len(content)))

    # ── Shake animation ───────────────────────────────────────────────────────

    def _do_shake(self):
        offsets = [(-4,1),(4,-1),(-3,2),(3,-2),(0,0)]
        self._shake_seq(offsets, 0)

    def _shake_seq(self, offsets, i):
        if i >= len(offsets):
            return
        dx, dy = offsets[i]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        self.root.after(45, lambda: self._shake_seq(offsets, i + 1))

    # ── Destruction ───────────────────────────────────────────────────────────

    def _obliterate(self):
        self.dead = True
        if self.tick_job:
            self.root.after_cancel(self.tick_job)

        self.text.delete("1.0", "end")
        self._update_stats()
        self.bar_canvas.itemconfig(self.bar_rect, fill=ACCENT_DANGER)
        self.bar_canvas.coords(self.bar_rect, 0, 0, 0, 4)
        self.count_var.set("0")
        self.status_var.set("Everything is gone.")

        # Show overlay
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lift()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset(self):
        if self.tick_job:
            self.root.after_cancel(self.tick_job)

        self.dead      = False
        self.started   = False
        self.last_type_ms = 0

        self.overlay.place_forget()

        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self._placeholder_active = False
        self._restore_placeholder()

        self.words_var.set("0")
        self.chars_var.set("0")
        self.count_var.set("—")
        self.status_var.set("Waiting for you to begin…")
        self.count_label.config(fg=MUTED)

        self.bar_canvas.update_idletasks()
        w = self.bar_canvas.winfo_width()
        self.bar_canvas.coords(self.bar_rect, 0, 0, w, 4)
        self.bar_canvas.itemconfig(self.bar_rect, fill=ACCENT_SAFE)

        self.text.focus_set()

    # ── Utility ───────────────────────────────────────────────────────────────

    @staticmethod
    def _now() -> int:
        return int(time.monotonic() * 1000)

    def _show_waiting(self):
        self.status_var.set("Waiting for you to begin…")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app  = DangerousWriterApp(root)
    root.mainloop()