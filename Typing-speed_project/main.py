"""
TypeRacer Pro — Typing Speed Test & Trainer
A Tkinter desktop app with WPM tracking, high scores, difficulty levels, and multiple text samples.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
import random

# ─────────────────────────────────────────────────────────────
#  Text Samples by Difficulty
# ─────────────────────────────────────────────────────────────
SAMPLES = {
    "Easy": [
        "The sun sets behind the mountains as the day comes to an end. Birds fly home to their nests and the sky turns shades of orange and pink. It is a beautiful evening to take a walk outside.",
        "She picked up the book from the shelf and opened it to the first page. The story began on a rainy afternoon in a small town by the sea. She smiled and settled into her favourite chair.",
        "My dog loves to play fetch in the park every morning. He runs as fast as he can and brings the ball back every time. We always stop for water before heading home.",
        "Learning to cook is one of the best skills you can have. You save money, eat healthier, and can share meals with people you love. Start simple and build your confidence one dish at a time.",
        "The library was quiet in the early hours of the morning. Rows of books lined the walls from floor to ceiling. A single lamp lit the reading corner near the window.",
    ],
    "Medium": [
        "Productivity is not about doing more things faster; it is about doing the right things with full attention. Many people confuse being busy with being effective. The most successful people protect their focus like a precious resource.",
        "The history of the internet is one of the most remarkable stories of human collaboration. What began as a military communications project evolved into a global network connecting billions of people across every continent.",
        "Photography teaches you to see the world differently. You start noticing light, shadow, and composition in everyday scenes. A great photograph does not require an expensive camera — it requires a curious and patient eye.",
        "Climate change is one of the defining challenges of our generation. Rising temperatures, shifting weather patterns, and melting ice caps are already affecting ecosystems around the world. Action at every level is needed.",
        "The human brain is capable of extraordinary adaptation. When we learn a new skill, neurons form new connections through a process called neuroplasticity. Practice and repetition literally reshape the physical structure of our minds.",
    ],
    "Hard": [
        "Epistemological frameworks in contemporary philosophy challenge our assumptions about justified belief and the nature of knowledge itself. The distinction between propositional and procedural knowledge remains a cornerstone of debates surrounding cognitive architecture.",
        "Quantum entanglement describes a phenomenon whereby two particles become correlated such that the quantum state of each particle cannot be described independently. Measuring one particle instantaneously influences its partner, regardless of the distance separating them.",
        "The socioeconomic ramifications of automation extend beyond simple job displacement. Structural unemployment disproportionately affects workers in routine cognitive and manual occupations, necessitating comprehensive retraining programmes and fundamental reconsideration of social safety networks.",
        "Byzantine fault tolerance algorithms, such as Practical Byzantine Fault Tolerance, allow distributed systems to reach consensus even when some nodes behave arbitrarily or maliciously. This property is foundational to the security of modern blockchain architectures.",
        "Thermodynamic entropy, as described by Boltzmann's statistical mechanics, quantifies the number of microscopic configurations consistent with a macroscopic state. The second law of thermodynamics asserts that entropy in an isolated system never decreases over time.",
    ],
}

DIFFICULTY_COLORS = {
    "Easy":   {"accent": "#00e5a0", "dim": "#00704e"},
    "Medium": {"accent": "#ffcc00", "dim": "#7a6200"},
    "Hard":   {"accent": "#ff5f7e", "dim": "#7a1e30"},
}

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "typing_scores.json")


# ─────────────────────────────────────────────────────────────
#  Score Persistence
# ─────────────────────────────────────────────────────────────
def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"Easy": [], "Medium": [], "Hard": []}


def save_scores(scores):
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────────────────────
class TypingApp(tk.Tk):
    BG       = "#0b0c10"
    PANEL    = "#12141a"
    BORDER   = "#1e2030"
    FG       = "#d4d8e8"
    FG_DIM   = "#4a5070"
    FG_MID   = "#7880a0"

    def __init__(self):
        super().__init__()
        self.title("TypeRacer Pro")
        self.configure(bg=self.BG)
        self.minsize(860, 620)
        self.resizable(True, True)

        self.scores = load_scores()
        self.difficulty = tk.StringVar(value="Medium")
        self.current_sample = ""
        self.start_time = None
        self.timer_running = False
        self.test_complete = False
        self._timer_id = None
        self._blink_id = None

        self._build_ui()
        self._new_test()

    # ── UI Construction ──────────────────────────────────────
    def _build_ui(self):
        # ── Top bar ──
        topbar = tk.Frame(self, bg=self.PANEL, height=56)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="TYPE", bg=self.PANEL, fg=self.FG,
                 font=("Georgia", 18, "bold")).pack(side="left", padx=(20, 0), pady=14)
        tk.Label(topbar, text="RACER", bg=self.PANEL, fg="#ffcc00",
                 font=("Georgia", 18, "bold")).pack(side="left", pady=14)
        tk.Label(topbar, text="PRO", bg=self.PANEL, fg=self.FG_DIM,
                 font=("Georgia", 10)).pack(side="left", padx=(6, 0), pady=18)

        # Difficulty switcher
        diff_frame = tk.Frame(topbar, bg=self.PANEL)
        diff_frame.pack(side="right", padx=20, pady=10)
        for d in ("Easy", "Medium", "Hard"):
            c = DIFFICULTY_COLORS[d]["accent"]
            rb = tk.Radiobutton(
                diff_frame, text=d, variable=self.difficulty, value=d,
                bg=self.PANEL, fg=self.FG_MID,
                selectcolor=self.PANEL, activebackground=self.PANEL,
                activeforeground=c,
                indicatoron=False,
                relief="flat", bd=0, padx=12, pady=4,
                font=("Courier New", 9, "bold"),
                command=self._on_difficulty_change,
            )
            rb.pack(side="left", padx=2)
            # Highlight selected
            if d == self.difficulty.get():
                rb.config(fg=c)
            self._style_radio(rb, d)

        # ── Stats row ──
        stats_frame = tk.Frame(self, bg=self.BG)
        stats_frame.pack(fill="x", padx=24, pady=(16, 0))

        self.stat_wpm   = self._stat_box(stats_frame, "WPM",      "—")
        self.stat_acc   = self._stat_box(stats_frame, "ACCURACY", "—")
        self.stat_time  = self._stat_box(stats_frame, "TIME",     "0s")
        self.stat_best  = self._stat_box(stats_frame, "BEST WPM", self._get_best())

        # ── Separator ──
        tk.Frame(self, bg=self.BORDER, height=1).pack(fill="x", padx=24, pady=(12, 0))

        # ── Sample text display ──
        sample_outer = tk.Frame(self, bg=self.PANEL, bd=0)
        sample_outer.pack(fill="x", padx=24, pady=(14, 0))

        self.sample_canvas = tk.Text(
            sample_outer,
            bg=self.PANEL, fg=self.FG_DIM,
            font=("Georgia", 13),
            wrap="word", relief="flat", bd=0,
            padx=20, pady=16,
            height=5,
            state="disabled",
            cursor="arrow",
            selectbackground=self.PANEL,
        )
        self.sample_canvas.pack(fill="x")
        self.sample_canvas.tag_configure("correct",  foreground="#00e5a0")
        self.sample_canvas.tag_configure("wrong",    foreground="#ff5f7e",
                                         background="#2a0a10")
        self.sample_canvas.tag_configure("cursor",   foreground=self.FG,
                                         underline=True)
        self.sample_canvas.tag_configure("pending",  foreground=self.FG_DIM)
        self.sample_canvas.tag_configure("extra",    foreground="#ff5f7e")

        # ── Input area ──
        input_frame = tk.Frame(self, bg=self.BG)
        input_frame.pack(fill="x", padx=24, pady=(10, 0))

        self.input_var = tk.StringVar()
        self.input_var.trace_add("write", self._on_type)

        self.input_box = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            bg=self.PANEL, fg=self.FG,
            insertbackground="#ffcc00",
            font=("Courier New", 14),
            relief="flat", bd=0,
        )
        self.input_box.pack(fill="x", ipady=14, padx=2)
        tk.Frame(input_frame, bg=self.BORDER, height=2).pack(fill="x", padx=2)

        self.input_hint = tk.Label(
            self, text="↑  Start typing to begin the test",
            bg=self.BG, fg=self.FG_DIM, font=("Courier New", 9)
        )
        self.input_hint.pack(pady=(6, 0))

        # ── Button row ──
        btn_row = tk.Frame(self, bg=self.BG)
        btn_row.pack(pady=(16, 0))

        self.btn_new = self._make_button(btn_row, "⟳  New Test",  self._new_test,  primary=True)
        self.btn_new.pack(side="left", padx=6)
        self._make_button(btn_row, "🏆  Scores",   self._show_scores, primary=False).pack(side="left", padx=6)
        self._make_button(btn_row, "✕  Reset",     self._reset_test,  primary=False).pack(side="left", padx=6)

        # ── Result banner (hidden initially) ──
        self.result_frame = tk.Frame(self, bg=self.BG)
        self.result_wpm_lbl  = tk.Label(self.result_frame, bg=self.BG, fg="#ffcc00",
                                         font=("Georgia", 38, "bold"))
        self.result_wpm_lbl.pack()
        self.result_sub_lbl  = tk.Label(self.result_frame, bg=self.BG, fg=self.FG_MID,
                                         font=("Courier New", 11))
        self.result_sub_lbl.pack()
        self.result_rank_lbl = tk.Label(self.result_frame, bg=self.BG, fg=self.FG_DIM,
                                         font=("Courier New", 9))
        self.result_rank_lbl.pack(pady=(4, 0))

        # ── High scores panel (hidden) ──
        self.scores_frame = tk.Frame(self, bg=self.PANEL, bd=0)

        self.input_box.focus_set()

    def _style_radio(self, rb, difficulty):
        """Re-style radio buttons on selection."""
        def refresh(*_):
            for child in rb.master.winfo_children():
                d = child.cget("text")
                if d in DIFFICULTY_COLORS:
                    c = DIFFICULTY_COLORS[d]["accent"]
                    if self.difficulty.get() == d:
                        child.config(fg=c, font=("Courier New", 9, "bold"))
                    else:
                        child.config(fg=self.FG_DIM, font=("Courier New", 9))
        self.difficulty.trace_add("write", refresh)

    def _stat_box(self, parent, label, value):
        frame = tk.Frame(parent, bg=self.PANEL, padx=20, pady=10)
        frame.pack(side="left", expand=True, fill="both", padx=(0, 8))
        tk.Label(frame, text=label, bg=self.PANEL, fg=self.FG_DIM,
                 font=("Courier New", 7, "bold")).pack(anchor="w")
        val_lbl = tk.Label(frame, text=value, bg=self.PANEL, fg=self.FG,
                           font=("Courier New", 20, "bold"))
        val_lbl.pack(anchor="w")
        return val_lbl

    def _make_button(self, parent, text, cmd, primary=False):
        if primary:
            btn = tk.Button(parent, text=text, command=cmd,
                            bg="#ffcc00", fg="#000", activebackground="#ffe066",
                            activeforeground="#000", relief="flat",
                            font=("Courier New", 10, "bold"), padx=18, pady=8,
                            cursor="hand2")
        else:
            btn = tk.Button(parent, text=text, command=cmd,
                            bg=self.PANEL, fg=self.FG_MID, activebackground=self.BORDER,
                            activeforeground=self.FG, relief="flat",
                            font=("Courier New", 10), padx=16, pady=8,
                            cursor="hand2")
        return btn

    # ── Test Logic ───────────────────────────────────────────
    def _new_test(self):
        self._stop_timer()
        self.test_complete = False
        diff = self.difficulty.get()
        self.current_sample = random.choice(SAMPLES[diff])
        self.start_time = None
        self.input_var.set("")
        self._render_sample("")
        self.stat_wpm.config(text="—", fg=self.FG)
        self.stat_acc.config(text="—", fg=self.FG)
        self.stat_time.config(text="0s", fg=self.FG)
        self.stat_best.config(text=self._get_best(), fg=self.FG)
        self.input_hint.config(text="↑  Start typing to begin the test")
        self.result_frame.pack_forget()
        self.scores_frame.pack_forget()
        self.input_box.config(state="normal")
        self.input_box.focus_set()

    def _reset_test(self):
        self._new_test()

    def _on_difficulty_change(self):
        self._new_test()

    def _on_type(self, *_):
        if self.test_complete:
            return
        typed = self.input_var.get()

        # Start timer on first keystroke
        if typed and self.start_time is None:
            self.start_time = time.time()
            self._tick()
            self.input_hint.config(text="")

        self._render_sample(typed)
        self._update_live_stats(typed)

        # Check completion
        if typed == self.current_sample:
            self._finish_test(typed)

    def _render_sample(self, typed):
        sample = self.current_sample
        self.sample_canvas.config(state="normal")
        self.sample_canvas.delete("1.0", "end")

        for i, ch in enumerate(sample):
            tag = "pending"
            if i < len(typed):
                tag = "correct" if typed[i] == ch else "wrong"
            elif i == len(typed):
                tag = "cursor"
            self.sample_canvas.insert("end", ch, tag)

        # Show extra characters typed beyond sample length
        if len(typed) > len(sample):
            self.sample_canvas.insert("end", typed[len(sample):], "extra")

        self.sample_canvas.config(state="disabled")

    def _update_live_stats(self, typed):
        if self.start_time is None:
            return
        elapsed = time.time() - self.start_time
        if elapsed < 0.5:
            return
        words_typed = len(typed.split())
        wpm = int(words_typed / (elapsed / 60))

        # Accuracy
        correct = sum(1 for a, b in zip(typed, self.current_sample) if a == b)
        acc = int(correct / max(len(typed), 1) * 100)

        accent = DIFFICULTY_COLORS[self.difficulty.get()]["accent"]
        self.stat_wpm.config(text=str(wpm), fg=accent)
        self.stat_acc.config(text=f"{acc}%", fg=accent)

    def _tick(self):
        if self.start_time and not self.test_complete:
            elapsed = int(time.time() - self.start_time)
            self.stat_time.config(text=f"{elapsed}s")
            self._timer_id = self.after(500, self._tick)

    def _stop_timer(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    def _finish_test(self, typed):
        self._stop_timer()
        self.test_complete = True
        elapsed = time.time() - self.start_time

        word_count = len(self.current_sample.split())
        wpm = int(word_count / (elapsed / 60))

        correct = sum(1 for a, b in zip(typed, self.current_sample) if a == b)
        acc = int(correct / len(self.current_sample) * 100)

        self.stat_wpm.config(text=str(wpm), fg="#ffcc00")
        self.stat_acc.config(text=f"{acc}%", fg="#ffcc00")
        self.stat_time.config(text=f"{elapsed:.1f}s", fg="#ffcc00")

        # Save score
        diff = self.difficulty.get()
        self.scores[diff].append({"wpm": wpm, "acc": acc, "time": round(elapsed, 1)})
        self.scores[diff].sort(key=lambda x: x["wpm"], reverse=True)
        self.scores[diff] = self.scores[diff][:10]
        save_scores(self.scores)

        best = self._get_best()
        self.stat_best.config(text=best, fg="#ffcc00")

        # Show result banner
        rank = self._rank_wpm(wpm)
        self.result_wpm_lbl.config(text=f"{wpm} WPM")
        self.result_sub_lbl.config(
            text=f"{acc}% accuracy  ·  {elapsed:.1f}s  ·  {word_count} words")
        self.result_rank_lbl.config(text=rank)
        self.result_frame.pack(pady=(12, 0))
        self.input_box.config(state="disabled")

    @staticmethod
    def _rank_wpm(wpm):
        if wpm < 20:  return "🐢  Beginner — keep practising!"
        if wpm < 40:  return "📝  Below average — you're improving!"
        if wpm < 60:  return "✅  Average typist (40–60 WPM)"
        if wpm < 80:  return "⚡  Above average — nice work!"
        if wpm < 100: return "🔥  Fast typist — impressive!"
        return              "🚀  Professional level — outstanding!"

    def _get_best(self):
        diff = self.difficulty.get()
        scores = self.scores.get(diff, [])
        if scores:
            return str(scores[0]["wpm"])
        return "—"

    # ── Scores Panel ────────────────────────────────────────
    def _show_scores(self):
        # Toggle
        if self.scores_frame.winfo_ismapped():
            self.scores_frame.pack_forget()
            return

        self.result_frame.pack_forget()

        # Rebuild content
        for w in self.scores_frame.winfo_children():
            w.destroy()

        diff = self.difficulty.get()
        accent = DIFFICULTY_COLORS[diff]["accent"]

        header = tk.Frame(self.scores_frame, bg=self.PANEL)
        header.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(header, text=f"🏆  TOP SCORES  —  {diff.upper()}",
                 bg=self.PANEL, fg=accent, font=("Courier New", 10, "bold")).pack(side="left")
        tk.Button(header, text="✕", command=self.scores_frame.pack_forget,
                  bg=self.PANEL, fg=self.FG_DIM, relief="flat",
                  font=("Courier New", 10), cursor="hand2").pack(side="right")

        tk.Frame(self.scores_frame, bg=self.BORDER, height=1).pack(fill="x", padx=16)

        scores = self.scores.get(diff, [])
        if not scores:
            tk.Label(self.scores_frame, text="No scores yet — complete a test!",
                     bg=self.PANEL, fg=self.FG_DIM, font=("Courier New", 10),
                     pady=12).pack()
        else:
            for i, s in enumerate(scores[:10]):
                row = tk.Frame(self.scores_frame, bg=self.PANEL)
                row.pack(fill="x", padx=16, pady=2)
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"  {i+1}."
                tk.Label(row, text=medal, bg=self.PANEL, fg=self.FG,
                         font=("Courier New", 11), width=4).pack(side="left")
                tk.Label(row, text=f"{s['wpm']} WPM", bg=self.PANEL, fg=accent,
                         font=("Courier New", 12, "bold"), width=10).pack(side="left")
                tk.Label(row, text=f"{s['acc']}% acc", bg=self.PANEL, fg=self.FG_MID,
                         font=("Courier New", 10), width=10).pack(side="left")
                tk.Label(row, text=f"{s['time']}s", bg=self.PANEL, fg=self.FG_DIM,
                         font=("Courier New", 10)).pack(side="left")

        clr_btn = tk.Button(self.scores_frame, text="Clear Scores",
                            command=lambda: self._clear_scores(diff),
                            bg=self.PANEL, fg="#ff5f7e", relief="flat",
                            font=("Courier New", 9), cursor="hand2", pady=6)
        clr_btn.pack(pady=(8, 12))

        self.scores_frame.pack(fill="x", padx=24, pady=(10, 0))

    def _clear_scores(self, diff):
        if messagebox.askyesno("Clear Scores", f"Clear all {diff} scores?"):
            self.scores[diff] = []
            save_scores(self.scores)
            self.stat_best.config(text="—")
            self._show_scores()


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = TypingApp()
    app.mainloop()