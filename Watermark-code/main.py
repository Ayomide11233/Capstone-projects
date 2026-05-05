"""
WatermarkStudio — A Tkinter + Pillow desktop app to add text or logo watermarks to images.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageEnhance
import os
import sys


# ─────────────────────────────────────────────
#  Helper: find a usable TrueType font
# ─────────────────────────────────────────────
def find_system_font(bold=False):
    candidates = []
    if sys.platform == "win32":
        base = r"C:\Windows\Fonts"
        candidates = (
            ["arialbd.ttf", "arial.ttf", "calibrib.ttf", "calibri.ttf"] if bold
            else ["arial.ttf", "calibri.ttf", "verdana.ttf"]
        )
        candidates = [os.path.join(base, f) for f in candidates]
    elif sys.platform == "darwin":
        bases = ["/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
        names = (
            ["Arial Bold.ttf", "Helvetica.ttc", "Arial.ttf"] if bold
            else ["Arial.ttf", "Helvetica.ttc", "Verdana.ttf"]
        )
        candidates = [os.path.join(b, n) for b in bases for n in names]
    else:  # Linux / WSL
        bases = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts")]
        for base in bases:
            for root, _, files in os.walk(base):
                for f in files:
                    if f.lower().endswith((".ttf", ".otf")):
                        candidates.append(os.path.join(root, f))

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


# ─────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────
class WatermarkApp(tk.Tk):
    POSITIONS = [
        "Top-Left", "Top-Center", "Top-Right",
        "Center",
        "Bottom-Left", "Bottom-Center", "Bottom-Right",
        "Tile",
    ]

    def __init__(self):
        super().__init__()
        self.title("WatermarkStudio")
        self.resizable(True, True)
        self.configure(bg="#0f0f0f")

        # State
        self.source_image: Image.Image | None = None
        self.logo_image: Image.Image | None = None
        self.preview_photo: ImageTk.PhotoImage | None = None
        self.watermark_color = "#ffffff"
        self.output_path: str | None = None

        self._build_styles()
        self._build_ui()
        self.minsize(920, 640)

    # ── Styles ──────────────────────────────
    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        bg, fg, accent, panel = "#0f0f0f", "#e8e8e0", "#c8ff00", "#1a1a1a"
        entry_bg = "#242424"

        style.configure(".", background=bg, foreground=fg, font=("Courier New", 10))
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground=fg, font=("Courier New", 10))
        style.configure("Panel.TLabel", background=panel, foreground=fg, font=("Courier New", 10))
        style.configure("Head.TLabel", background=bg, foreground=accent,
                        font=("Courier New", 13, "bold"))
        style.configure("TEntry", fieldbackground=entry_bg, foreground=fg,
                        insertcolor=fg, borderwidth=0, relief="flat")
        style.configure("TCombobox", fieldbackground=entry_bg, foreground=fg,
                        background=entry_bg, arrowcolor=accent)
        style.map("TCombobox", fieldbackground=[("readonly", entry_bg)])
        style.configure("TScale", background=panel, troughcolor="#333",
                        sliderlength=16, sliderrelief="flat")
        style.configure("Accent.TButton",
                        background=accent, foreground="#000000",
                        font=("Courier New", 10, "bold"),
                        borderwidth=0, relief="flat", padding=(12, 8))
        style.map("Accent.TButton",
                  background=[("active", "#aadd00"), ("pressed", "#88bb00")])
        style.configure("Ghost.TButton",
                        background="#242424", foreground=fg,
                        font=("Courier New", 10),
                        borderwidth=0, relief="flat", padding=(10, 6))
        style.map("Ghost.TButton",
                  background=[("active", "#333"), ("pressed", "#111")])
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background="#1a1a1a", foreground="#888",
                        font=("Courier New", 10), padding=(14, 6))
        style.map("TNotebook.Tab",
                  background=[("selected", bg)],
                  foreground=[("selected", accent)])

    # ── UI Layout ───────────────────────────
    def _build_ui(self):
        # Header bar
        header = ttk.Frame(self)
        header.pack(fill="x", padx=0, pady=0)
        header.configure(style="TFrame")
        tk.Frame(header, bg="#c8ff00", height=3).pack(fill="x")
        inner_h = ttk.Frame(header)
        inner_h.pack(fill="x", padx=20, pady=10)
        ttk.Label(inner_h, text="◈ WATERMARK", style="Head.TLabel").pack(side="left")
        ttk.Label(inner_h, text="STUDIO", foreground="#888",
                  font=("Courier New", 13), background="#0f0f0f").pack(side="left", padx=(4, 0))

        # Main body
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        left = ttk.Frame(body, style="Panel.TFrame", width=280)
        left.pack(side="left", fill="y", padx=(0, 10), pady=0)
        left.pack_propagate(False)

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        self._build_controls(left)
        self._build_preview(right)

    def _build_controls(self, parent):
        px = dict(padx=14)  # only padx — pady is always specified explicitly

        # ── Image section ──
        ttk.Label(parent, text="IMAGE", style="Head.TLabel", font=("Courier New", 10, "bold")).pack(anchor="w", padx=14, pady=(14, 2))
        ttk.Button(parent, text="▸ Open Image", style="Ghost.TButton",
                   command=self._open_image).pack(fill="x", padx=14, pady=2)
        self.img_label = ttk.Label(parent, text="No image loaded", style="Panel.TLabel",
                                   foreground="#555", font=("Courier New", 8))
        self.img_label.pack(anchor="w", padx=14, pady=4)

        ttk.Separator(parent).pack(fill="x", padx=14, pady=8)

        # ── Watermark type tabs ──
        ttk.Label(parent, text="WATERMARK", style="Head.TLabel",
                  font=("Courier New", 10, "bold")).pack(anchor="w", padx=14, pady=(0, 4))

        self.nb = ttk.Notebook(parent)
        self.nb.pack(fill="x", padx=14)

        text_tab = ttk.Frame(self.nb, style="Panel.TFrame")
        logo_tab = ttk.Frame(self.nb, style="Panel.TFrame")
        self.nb.add(text_tab, text=" Text ")
        self.nb.add(logo_tab, text=" Logo ")

        self._build_text_tab(text_tab)
        self._build_logo_tab(logo_tab)

        ttk.Separator(parent).pack(fill="x", padx=14, pady=8)

        # ── Position & Opacity ──
        ttk.Label(parent, text="PLACEMENT", style="Head.TLabel",
                  font=("Courier New", 10, "bold")).pack(anchor="w", padx=14, pady=(0, 4))

        ttk.Label(parent, text="Position", style="Panel.TLabel").pack(anchor="w", padx=14, pady=4)
        self.pos_var = tk.StringVar(value="Bottom-Right")
        pos_cb = ttk.Combobox(parent, textvariable=self.pos_var,
                              values=self.POSITIONS, state="readonly")
        pos_cb.pack(fill="x", padx=14, pady=2)
        pos_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_preview())

        ttk.Label(parent, text="Opacity", style="Panel.TLabel").pack(anchor="w", padx=14, pady=4)
        self.opacity_var = tk.IntVar(value=80)
        opacity_scale = ttk.Scale(parent, from_=10, to=100,
                                  variable=self.opacity_var, orient="horizontal",
                                  command=lambda v: self._refresh_preview())
        opacity_scale.pack(fill="x", padx=14, pady=2)
        self.opacity_lbl = ttk.Label(parent, text="80%", style="Panel.TLabel",
                                     foreground="#c8ff00")
        self.opacity_lbl.pack(anchor="e", padx=14)

        def _upd_opacity_lbl(*_):
            self.opacity_lbl.config(text=f"{self.opacity_var.get()}%")
        self.opacity_var.trace_add("write", _upd_opacity_lbl)

        ttk.Label(parent, text="Margin (px)", style="Panel.TLabel").pack(anchor="w", padx=14, pady=4)
        self.margin_var = tk.IntVar(value=20)
        ttk.Scale(parent, from_=0, to=100, variable=self.margin_var, orient="horizontal",
                  command=lambda v: self._refresh_preview()).pack(fill="x", padx=14, pady=2)

        ttk.Separator(parent).pack(fill="x", padx=14, pady=8)

        # ── Export ──
        ttk.Button(parent, text="⬇  Save Watermarked Image",
                   style="Accent.TButton", command=self._save_image).pack(
            fill="x", padx=14, pady=(4, 14))

    def _build_text_tab(self, parent):
        p = dict(padx=8, pady=3)
        ttk.Label(parent, text="Text", style="Panel.TLabel").pack(anchor="w", **p)
        self.wm_text = tk.StringVar(value="© YourBrand.com")
        e = tk.Entry(parent, textvariable=self.wm_text, bg="#242424",
                     fg="#e8e8e0", insertbackground="#e8e8e0",
                     relief="flat", font=("Courier New", 10), bd=4)
        e.pack(fill="x", padx=8, pady=2)
        self.wm_text.trace_add("write", lambda *_: self._refresh_preview())

        ttk.Label(parent, text="Font size", style="Panel.TLabel").pack(anchor="w", **p)
        self.font_size = tk.IntVar(value=36)
        ttk.Scale(parent, from_=10, to=120, variable=self.font_size,
                  orient="horizontal",
                  command=lambda v: self._refresh_preview()).pack(fill="x", padx=8)

        ttk.Label(parent, text="Color", style="Panel.TLabel").pack(anchor="w", **p)
        self.color_btn = tk.Button(parent, bg=self.watermark_color, width=4,
                                   relief="flat", cursor="hand2",
                                   command=self._pick_color)
        self.color_btn.pack(anchor="w", padx=8, pady=2)

        ttk.Label(parent, text="Style", style="Panel.TLabel").pack(anchor="w", **p)
        self.bold_var = tk.BooleanVar(value=True)
        self.italic_var = tk.BooleanVar()
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(anchor="w", padx=8)
        tk.Checkbutton(row, text="Bold", variable=self.bold_var,
                       bg="#1a1a1a", fg="#e8e8e0", selectcolor="#333",
                       activebackground="#1a1a1a", activeforeground="#c8ff00",
                       command=self._refresh_preview).pack(side="left")
        tk.Checkbutton(row, text="Italic", variable=self.italic_var,
                       bg="#1a1a1a", fg="#e8e8e0", selectcolor="#333",
                       activebackground="#1a1a1a", activeforeground="#c8ff00",
                       command=self._refresh_preview).pack(side="left", padx=8)

        ttk.Label(parent, text="Shadow", style="Panel.TLabel").pack(anchor="w", **p)
        self.shadow_var = tk.BooleanVar(value=True)
        tk.Checkbutton(parent, text="Drop shadow", variable=self.shadow_var,
                       bg="#1a1a1a", fg="#e8e8e0", selectcolor="#333",
                       activebackground="#1a1a1a", activeforeground="#c8ff00",
                       command=self._refresh_preview).pack(anchor="w", padx=8, pady=(0, 8))

    def _build_logo_tab(self, parent):
        p = dict(padx=8, pady=4)
        ttk.Button(parent, text="▸ Open Logo (PNG/SVG)",
                   style="Ghost.TButton",
                   command=self._open_logo).pack(fill="x", **p)
        self.logo_label = ttk.Label(parent, text="No logo loaded", style="Panel.TLabel",
                                    foreground="#555", font=("Courier New", 8))
        self.logo_label.pack(anchor="w", **p)

        ttk.Label(parent, text="Scale (%)", style="Panel.TLabel").pack(anchor="w", **p)
        self.logo_scale = tk.IntVar(value=20)
        ttk.Scale(parent, from_=5, to=80, variable=self.logo_scale,
                  orient="horizontal",
                  command=lambda v: self._refresh_preview()).pack(fill="x", padx=8, pady=(0, 8))

    def _build_preview(self, parent):
        ttk.Label(parent, text="PREVIEW", foreground="#555",
                  font=("Courier New", 9)).pack(anchor="w", pady=(4, 4))
        self.canvas = tk.Canvas(parent, bg="#141414", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._refresh_preview())
        self._draw_placeholder()

    def _draw_placeholder(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width() or 600, self.canvas.winfo_height() or 400
        self.canvas.create_text(w // 2, h // 2,
                                text="Open an image to begin",
                                fill="#333", font=("Courier New", 13))

    # ── Actions ────────────────────────────
    def _open_image(self):
        path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"), ("All", "*.*")])
        if not path:
            return
        self.source_image = Image.open(path).convert("RGBA")
        name = os.path.basename(path)
        self.img_label.config(text=f"{name}  {self.source_image.width}×{self.source_image.height}")
        self._refresh_preview()

    def _open_logo(self):
        path = filedialog.askopenfilename(
            title="Open Logo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All", "*.*")])
        if not path:
            return
        self.logo_image = Image.open(path).convert("RGBA")
        self.logo_label.config(text=os.path.basename(path))
        self._refresh_preview()

    def _pick_color(self):
        color = colorchooser.askcolor(color=self.watermark_color, title="Watermark color")[1]
        if color:
            self.watermark_color = color
            self.color_btn.config(bg=color)
            self._refresh_preview()

    def _save_image(self):
        if not self.source_image:
            messagebox.showwarning("No image", "Please open an image first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All", "*.*")],
            title="Save Watermarked Image")
        if not path:
            return
        result = self._apply_watermark(self.source_image.copy())
        result.convert("RGB").save(path)
        messagebox.showinfo("Saved!", f"Image saved to:\n{path}")

    # ── Watermark engine ───────────────────
    def _apply_watermark(self, img: Image.Image) -> Image.Image:
        tab = self.nb.index("current")  # 0=text, 1=logo
        opacity = self.opacity_var.get()
        pos_key = self.pos_var.get()
        margin = self.margin_var.get()

        if tab == 0:
            return self._apply_text_watermark(img, opacity, pos_key, margin)
        else:
            return self._apply_logo_watermark(img, opacity, pos_key, margin)

    def _apply_text_watermark(self, img, opacity, pos_key, margin):
        text = self.wm_text.get().strip() or "© Watermark"
        size = max(10, self.font_size.get())

        # Load font
        font_path = find_system_font(bold=self.bold_var.get())
        try:
            font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        draw_dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = draw_dummy.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Parse color + opacity
        r, g, b = self._hex_to_rgb(self.watermark_color)
        alpha = int(opacity / 100 * 255)

        if pos_key == "Tile":
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            step_x, step_y = tw + 60, th + 60
            for y in range(-th, img.height + th, step_y):
                for x in range(-tw, img.width + tw, step_x):
                    if self.shadow_var.get():
                        ld.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, alpha // 2))
                    ld.text((x, y), text, font=font, fill=(r, g, b, alpha))
            img = Image.alpha_composite(img, layer)
        else:
            x, y = self._compute_position(pos_key, img.size, (tw, th), margin)
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            if self.shadow_var.get():
                ld.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, alpha // 2))
            ld.text((x, y), text, font=font, fill=(r, g, b, alpha))
            img = Image.alpha_composite(img, layer)
        return img

    def _apply_logo_watermark(self, img, opacity, pos_key, margin):
        if not self.logo_image:
            messagebox.showwarning("No logo", "Please load a logo image first.")
            return img

        scale = self.logo_scale.get() / 100
        new_w = max(1, int(img.width * scale))
        ratio = new_w / self.logo_image.width
        new_h = max(1, int(self.logo_image.height * ratio))
        logo = self.logo_image.resize((new_w, new_h), Image.LANCZOS)

        # Apply opacity to logo alpha channel
        r_ch, g_ch, b_ch, a_ch = logo.split()
        a_ch = a_ch.point(lambda p: int(p * opacity / 100))
        logo = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))

        if pos_key == "Tile":
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            for y in range(0, img.height, new_h + 30):
                for x in range(0, img.width, new_w + 30):
                    layer.paste(logo, (x, y), logo)
            img = Image.alpha_composite(img, layer)
        else:
            x, y = self._compute_position(pos_key, img.size, (new_w, new_h), margin)
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            layer.paste(logo, (x, y), logo)
            img = Image.alpha_composite(img, layer)
        return img

    @staticmethod
    def _compute_position(pos_key, img_size, wm_size, margin):
        iw, ih = img_size
        ww, wh = wm_size
        positions = {
            "Top-Left":      (margin, margin),
            "Top-Center":    ((iw - ww) // 2, margin),
            "Top-Right":     (iw - ww - margin, margin),
            "Center":        ((iw - ww) // 2, (ih - wh) // 2),
            "Bottom-Left":   (margin, ih - wh - margin),
            "Bottom-Center": ((iw - ww) // 2, ih - wh - margin),
            "Bottom-Right":  (iw - ww - margin, ih - wh - margin),
        }
        return positions.get(pos_key, (margin, margin))

    @staticmethod
    def _hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # ── Preview ────────────────────────────
    def _refresh_preview(self, *_):
        if not self.source_image:
            self._draw_placeholder()
            return
        self.after_idle(self._do_refresh)

    def _do_refresh(self):
        if not self.source_image:
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        preview_src = self.source_image.copy()
        watermarked = self._apply_watermark(preview_src)

        # Fit to canvas
        ratio = min(cw / watermarked.width, ch / watermarked.height)
        nw, nh = int(watermarked.width * ratio), int(watermarked.height * ratio)
        thumb = watermarked.resize((nw, nh), Image.LANCZOS).convert("RGB")

        self.preview_photo = ImageTk.PhotoImage(thumb)
        self.canvas.delete("all")
        x, y = (cw - nw) // 2, (ch - nh) // 2
        self.canvas.create_rectangle(x - 1, y - 1, x + nw + 1, y + nh + 1,
                                     outline="#c8ff00", width=1)
        self.canvas.create_image(x, y, anchor="nw", image=self.preview_photo)
        self.canvas.create_text(cw - 8, ch - 6,
                                text=f"{self.source_image.width}×{self.source_image.height}",
                                anchor="se", fill="#444", font=("Courier New", 8))


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = WatermarkApp()
    app.mainloop()