import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import os
import re
import tempfile
import shutil

OUTPUT_DIR = os.path.expanduser("~/Downloads")


def is_valid_youtube_url(url):
    patterns = [
        r"youtube\.com/shorts/[\w-]+",
        r"youtu\.be/[\w-]+",
        r"youtube\.com/watch\?v=[\w-]+",
    ]
    return any(re.search(p, url) for p in patterns)


def download_and_convert(url, output_dir, fps_var, scale_var, on_progress, on_done, on_error):
    tmpdir = tempfile.mkdtemp(prefix="shortgif_")
    try:
        on_progress("영상 다운로드 중...")
        dl_cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(tmpdir, "video.%(ext)s"),
            url,
        ]
        result = subprocess.run(dl_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"다운로드 실패:\n{result.stderr[-500:]}")

        video_files = [f for f in os.listdir(tmpdir) if f.startswith("video.")]
        if not video_files:
            raise RuntimeError("다운로드된 파일을 찾을 수 없습니다.")
        video_path = os.path.join(tmpdir, video_files[0])

        on_progress("팔레트 생성 중...")
        palette_path = os.path.join(tmpdir, "palette.png")
        scale = scale_var.get()
        fps = fps_var.get()

        palette_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"fps={fps},scale={scale}:-1:flags=lanczos,palettegen=stats_mode=diff",
            palette_path,
        ]
        result = subprocess.run(palette_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"팔레트 생성 실패:\n{result.stderr[-300:]}")

        on_progress("GIF 변환 중...")

        video_id_match = re.search(r"shorts/([\w-]+)|v=([\w-]+)|youtu\.be/([\w-]+)", url)
        video_id = next((g for g in (video_id_match.groups() if video_id_match else []) if g), "output")
        gif_name = f"{video_id}.gif"
        gif_path = os.path.join(output_dir, gif_name)

        gif_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", palette_path,
            "-lavfi", f"fps={fps},scale={scale}:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5",
            gif_path,
        ]
        result = subprocess.run(gif_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"GIF 변환 실패:\n{result.stderr[-300:]}")

        on_done(gif_path)
    except Exception as e:
        on_error(str(e))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Neumorphism Design System ──────────────────────────────────────────────────
NEU_BG      = "#e0e5ec"   # single unified background
NEU_LIGHT   = "#ffffff"   # highlight shadow color
NEU_DARK    = "#a3b1c6"   # depth shadow color
NEU_TEXT    = "#31456a"   # primary text
NEU_TEXT_S  = "#8899aa"   # secondary / muted text
NEU_ACCENT  = "#5b84b1"   # accent blue
NEU_GREEN   = "#4e9a6a"   # success green
NEU_RED     = "#aa4444"   # error red

NEU_FONT    = ("Helvetica Neue", 12)
NEU_FONT_B  = ("Helvetica Neue", 13, "bold")
NEU_FONT_SM = ("Helvetica Neue", 10)
NEU_FONT_H  = ("Helvetica Neue", 20, "bold")
NEU_FONT_CAP = ("Helvetica Neue", 9)

SD = 5   # shadow depth (offset pixels)
SR = 12  # default corner radius


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def fill_rrect(canvas, x1, y1, x2, y2, r, color):
    """Fill a rounded rectangle on a Canvas."""
    r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline="")
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline="")
    if r > 0:
        for ox, oy in ((x1, y1), (x2 - 2*r, y1), (x1, y2 - 2*r), (x2 - 2*r, y2 - 2*r)):
            canvas.create_oval(ox, oy, ox + 2*r, oy + 2*r, fill=color, outline="")


def draw_raised(canvas, x1, y1, x2, y2, r=SR, steps=SD):
    """Draw neumorphic raised (extruded) shadow layers, then fill face."""
    for i in range(steps, 0, -1):
        t = i / steps
        light = lerp_color(NEU_BG, NEU_LIGHT, t * 0.85)
        dark  = lerp_color(NEU_BG, NEU_DARK,  t * 0.65)
        fill_rrect(canvas, x1 - i, y1 - i, x2 - i, y2 - i, r, light)
        fill_rrect(canvas, x1 + i, y1 + i, x2 + i, y2 + i, r, dark)
    fill_rrect(canvas, x1, y1, x2, y2, r, NEU_BG)


def draw_inset(canvas, x1, y1, x2, y2, r=SR, steps=SD):
    """Draw neumorphic inset (pressed) shadow layers."""
    fill_rrect(canvas, x1, y1, x2, y2, r, NEU_BG)
    for i in range(1, steps + 1):
        t = i / steps
        dark  = lerp_color(NEU_BG, NEU_DARK,  t * 0.45)
        light = lerp_color(NEU_BG, NEU_LIGHT, t * 0.70)
        x1c, y1c, x2c, y2c = x1 + r//2, y1 + r//2, x2 - r//2, y2 - r//2
        if y1c + i <= y2c:
            canvas.create_line(x1c, y1c + i, x2c, y1c + i, fill=dark)
        if x1c + i <= x2c:
            canvas.create_line(x1c + i, y1c, x1c + i, y2c, fill=dark)
        if y2c - i >= y1c:
            canvas.create_line(x1c, y2c - i, x2c, y2c - i, fill=light)
        if x2c - i >= x1c:
            canvas.create_line(x2c - i, y1c, x2c - i, y2c, fill=light)


class NeuButton(tk.Canvas):
    """Neumorphic button: raised at rest, inset when pressed."""

    def __init__(self, parent, text="", command=None,
                 min_width=80, padx=20, pady=10,
                 font=None, color=None, bg=None):
        self._text    = text
        self._command = command
        self._state   = "normal"
        self._color   = color or NEU_TEXT   # text/icon accent color
        self._pressed = False
        self._inside  = False
        self._font    = font or NEU_FONT
        self._cbg     = bg or NEU_BG

        tmp = tk.Label(parent, text=text, font=self._font)
        tmp.update_idletasks()
        tw = max(tmp.winfo_reqwidth(), min_width - 2 * padx)
        th = tmp.winfo_reqheight()
        tmp.destroy()

        self._bw = tw + 2 * padx
        self._bh = th + 2 * pady

        # Canvas larger than face to accommodate outer shadow
        cw = self._bw + 2 * SD
        ch = self._bh + 2 * SD

        super().__init__(parent, width=cw, height=ch,
                         bd=0, highlightthickness=0, cursor="arrow",
                         bg=self._cbg)
        self._render()
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)

    def _render(self, pressed=False):
        self.delete("all")
        x1, y1 = SD, SD
        x2, y2 = self._bw + SD, self._bh + SD

        if pressed or self._state == "disabled":
            draw_inset(self, x1, y1, x2, y2)
        else:
            draw_raised(self, x1, y1, x2, y2)

        text_c = NEU_TEXT_S if self._state == "disabled" else self._color
        ox = 1 if pressed else 0
        self.create_text((x1 + x2) // 2 + ox, (y1 + y2) // 2 + ox,
                         text=self._text, font=self._font, fill=text_c)

    def config(self, **kw):
        changed = False
        if "state" in kw:
            self._state = kw["state"]
            changed = True
        if "text" in kw:
            self._text = kw["text"]
            changed = True
        if changed:
            self._render(pressed=self._pressed)

    def configure(self, **kw):
        self.config(**kw)

    def _on_press(self, e):
        if self._state == "disabled":
            return
        self._pressed = True
        self._render(pressed=True)

    def _on_release(self, e):
        if self._state == "disabled":
            return
        was_pressed = self._pressed
        self._pressed = False
        self._render(pressed=False)
        if was_pressed and self._inside and self._command:
            self._command()

    def _on_enter(self, e):
        self._inside = True

    def _on_leave(self, e):
        self._inside = False
        if self._pressed:
            self._pressed = False
            self._render(pressed=False)


class NeuEntry(tk.Canvas):
    """Neumorphic inset container that embeds a tk.Entry."""

    def __init__(self, parent, textvariable=None, width=40,
                 font=None, state="normal", bg=None):
        self._cbg  = bg or NEU_BG
        self._font = font or NEU_FONT
        pad = 8

        tmp = tk.Label(parent, text="W" * width, font=self._font)
        tmp.update_idletasks()
        tw = tmp.winfo_reqwidth()
        th = tmp.winfo_reqheight()
        tmp.destroy()

        self._ew = tw
        self._eh = th + pad * 2

        cw = self._ew + 2 * SD + pad * 2
        ch = self._eh + 2 * SD

        super().__init__(parent, width=cw, height=ch,
                         bd=0, highlightthickness=0, bg=self._cbg)

        x1, y1 = SD, SD
        x2, y2 = cw - SD, ch - SD
        draw_inset(self, x1, y1, x2, y2, r=10)

        self.entry = tk.Entry(self,
                               textvariable=textvariable,
                               font=self._font,
                               bg=NEU_BG, fg=NEU_TEXT,
                               insertbackground=NEU_TEXT,
                               relief="flat", bd=0,
                               width=width,
                               state=state)
        self.create_window(cw // 2, ch // 2,
                           window=self.entry, width=self._ew)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube → GIF")
        self.resizable(False, False)
        self.configure(bg=NEU_BG)
        self._apply_style()
        self._build_ui()
        self._check_clipboard_on_focus()

    def _apply_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Neu.Horizontal.TProgressbar",
                        troughcolor=lerp_color(NEU_BG, NEU_DARK, 0.3),
                        background=NEU_ACCENT,
                        borderwidth=0,
                        thickness=8)
        style.configure("TCombobox",
                        fieldbackground=NEU_BG,
                        background=NEU_BG,
                        foreground=NEU_TEXT,
                        selectbackground=NEU_ACCENT,
                        selectforeground="#ffffff",
                        borderwidth=0,
                        relief="flat")
        self.option_add("*TCombobox*Listbox.background",       NEU_BG)
        self.option_add("*TCombobox*Listbox.foreground",       NEU_TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", NEU_ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font",             NEU_FONT)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _label(self, parent, text, font=None, color=None, **pack_kw):
        tk.Label(parent, text=text,
                 font=font or NEU_FONT,
                 bg=NEU_BG, fg=color or NEU_TEXT
                 ).pack(**pack_kw)

    def _cap(self, parent, text):
        tk.Label(parent, text=text.upper(),
                 font=NEU_FONT_CAP, bg=NEU_BG, fg=NEU_TEXT_S,
                 anchor="w").pack(fill="x", padx=SD + 2, pady=(0, 2))

    def _section(self, parent, title=None):
        """Neu raised panel container."""
        if title:
            self._cap(parent, title)
        panel = tk.Canvas(parent, bg=NEU_BG, bd=0, highlightthickness=0)
        panel.pack(fill="x", padx=4, pady=(0, 16))

        def draw(event=None):
            panel.delete("shadow")
            w = panel.winfo_width()
            h = panel.winfo_height()
            if w < 2 or h < 2:
                return
            r = 16
            for i in range(SD, 0, -1):
                t = i / SD
                fill_rrect(panel, -i, -i, w + i - 1, h + i - 1, r,
                           lerp_color(NEU_BG, NEU_LIGHT, t * 0.75))
                fill_rrect(panel, i, i, w - i - 1, h - i - 1, r,
                           lerp_color(NEU_BG, NEU_DARK,  t * 0.55))
            fill_rrect(panel, 0, 0, w - 1, h - 1, r, NEU_BG)

        panel.bind("<Configure>", draw)
        inner = tk.Frame(panel, bg=NEU_BG)
        panel.create_window(0, 0, window=inner, anchor="nw")

        def resize(event=None):
            panel.config(width=inner.winfo_reqwidth(),
                         height=inner.winfo_reqheight())

        inner.bind("<Configure>", resize)
        return inner

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = tk.Frame(self, bg=NEU_BG, padx=28, pady=24)
        outer.pack(fill="both")

        # Header
        tk.Label(outer, text="YouTube  →  GIF",
                 font=NEU_FONT_H, bg=NEU_BG, fg=NEU_TEXT
                 ).pack(pady=(0, 20))

        # ── URL ───────────────────────────────────────────────────────
        self._cap(outer, "YouTube URL")
        url_row = tk.Frame(outer, bg=NEU_BG)
        url_row.pack(fill="x", pady=(0, 18))

        self.url_var = tk.StringVar()
        url_entry = NeuEntry(url_row, textvariable=self.url_var, width=38)
        url_entry.pack(side="left")
        self.url_entry = url_entry.entry

        NeuButton(url_row, "붙여넣기", self._paste_url,
                  min_width=90, padx=14, pady=10,
                  font=NEU_FONT_SM, color=NEU_ACCENT
                  ).pack(side="left", padx=(6, 0))

        # ── Options ───────────────────────────────────────────────────
        self._cap(outer, "변환 옵션")
        opt_inner = self._section(outer)
        opt_inner.configure(padx=16, pady=14)

        opt_row = tk.Frame(opt_inner, bg=NEU_BG)
        opt_row.pack(fill="x")

        # FPS
        tk.Label(opt_row, text="FPS", font=NEU_FONT,
                 bg=NEU_BG, fg=NEU_TEXT_S, width=9, anchor="w").pack(side="left")
        self.fps_var = tk.IntVar(value=15)
        tk.Spinbox(opt_row, from_=5, to=30, increment=5,
                   textvariable=self.fps_var,
                   width=4, font=NEU_FONT,
                   bg=NEU_BG, fg=NEU_TEXT,
                   buttonbackground=NEU_BG,
                   relief="flat", bd=0).pack(side="left", padx=(0, 24))

        # Scale
        tk.Label(opt_row, text="가로 크기", font=NEU_FONT,
                 bg=NEU_BG, fg=NEU_TEXT_S).pack(side="left")
        self.scale_var = tk.IntVar(value=480)
        ttk.Combobox(opt_row, textvariable=self.scale_var,
                     values=[240, 320, 480, 640, 720],
                     width=7, state="readonly",
                     font=NEU_FONT).pack(side="left", padx=(6, 0))

        tk.Frame(opt_inner, bg=lerp_color(NEU_BG, NEU_DARK, 0.25),
                 height=1).pack(fill="x", pady=12)

        dir_row = tk.Frame(opt_inner, bg=NEU_BG)
        dir_row.pack(fill="x")

        tk.Label(dir_row, text="저장 위치", font=NEU_FONT,
                 bg=NEU_BG, fg=NEU_TEXT_S, width=9, anchor="w").pack(side="left")
        self.outdir_var = tk.StringVar(value=OUTPUT_DIR)
        tk.Entry(dir_row, textvariable=self.outdir_var,
                 font=NEU_FONT_SM, bg=NEU_BG, fg=NEU_TEXT_S,
                 relief="flat", bd=0, width=26,
                 state="readonly").pack(side="left", fill="x", expand=True)
        NeuButton(dir_row, "찾기", self._choose_dir,
                  min_width=60, padx=12, pady=6,
                  font=NEU_FONT_SM, color=NEU_ACCENT
                  ).pack(side="right")

        # ── Convert ───────────────────────────────────────────────────
        self.convert_btn = NeuButton(outer,
                                      "GIF 변환 시작", self._start_conversion,
                                      min_width=400, padx=24, pady=14,
                                      font=NEU_FONT_B, color=NEU_GREEN)
        self.convert_btn.pack(pady=(6, 18))

        # ── Status ────────────────────────────────────────────────────
        self._cap(outer, "상태")
        status_inner = self._section(outer)
        status_inner.configure(padx=16, pady=14)

        self.progress_lbl = tk.Label(status_inner, text="대기 중...",
                                      font=NEU_FONT, bg=NEU_BG, fg=NEU_TEXT_S,
                                      anchor="w")
        self.progress_lbl.pack(fill="x")

        self.progress = ttk.Progressbar(status_inner, mode="indeterminate",
                                         length=420,
                                         style="Neu.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(10, 0))

        # ── Result ────────────────────────────────────────────────────
        self.result_frame = tk.Frame(outer, bg=NEU_BG)
        self.result_frame.pack(fill="x")

        self.result_lbl = tk.Label(self.result_frame, text="",
                                    font=NEU_FONT_SM, bg=NEU_BG, fg=NEU_TEXT,
                                    wraplength=400, justify="left", anchor="w")
        self.result_lbl.pack(side="left", fill="x", expand=True)

        self.open_btn = NeuButton(self.result_frame, "Finder 열기",
                                   self._open_in_finder,
                                   min_width=100, padx=14, pady=8,
                                   font=NEU_FONT_SM, color=NEU_ACCENT)
        self._last_gif = None

    # ── Event handlers ─────────────────────────────────────────────────────────
    def _check_clipboard_on_focus(self):
        self.bind("<FocusIn>", self._on_focus)

    def _on_focus(self, event):
        try:
            clip = self.clipboard_get()
            if is_valid_youtube_url(clip) and not self.url_var.get():
                self.url_var.set(clip)
        except Exception:
            pass

    def _paste_url(self):
        try:
            self.url_var.set(self.clipboard_get())
        except Exception:
            pass

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.outdir_var.get())
        if d:
            self.outdir_var.set(d)

    def _start_conversion(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL 없음", "YouTube URL을 입력하세요.")
            return
        if not is_valid_youtube_url(url):
            messagebox.showwarning("잘못된 URL", "유효한 YouTube URL이 아닙니다.")
            return

        self.convert_btn.config(state="disabled")
        self.result_lbl.config(text="")
        self.open_btn.pack_forget()
        self._last_gif = None
        self.progress.start(12)

        threading.Thread(
            target=download_and_convert,
            args=(url, self.outdir_var.get(), self.fps_var, self.scale_var,
                  self._on_progress, self._on_done, self._on_error),
            daemon=True,
        ).start()

    def _on_progress(self, msg):
        self.after(0, lambda: self.progress_lbl.config(text=msg, fg=NEU_TEXT_S))

    def _on_done(self, gif_path):
        self._last_gif = gif_path
        size_mb = os.path.getsize(gif_path) / 1024 / 1024
        self.after(0, lambda: self._finish(
            f"저장 완료: {gif_path}  ({size_mb:.1f} MB)", success=True))

    def _on_error(self, msg):
        self.after(0, lambda: self._finish(msg, success=False))

    def _finish(self, msg, success):
        self.progress.stop()
        self.convert_btn.config(state="normal")
        self.progress_lbl.config(
            text="완료!" if success else "오류 발생",
            fg=NEU_GREEN if success else NEU_RED)
        self.result_lbl.config(
            text=msg,
            fg=NEU_TEXT if success else NEU_RED)
        if success and self._last_gif:
            self.open_btn.pack(side="right", padx=(8, 0))

    def _open_in_finder(self):
        if self._last_gif and os.path.exists(self._last_gif):
            subprocess.run(["open", "-R", self._last_gif])


if __name__ == "__main__":
    app = App()
    app.mainloop()
