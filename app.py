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


# ── Windows 2000 Aesthetic — text ×2 ──────────────────────────────────────────
W2K_BG       = "#d4d0c8"
W2K_DARK     = "#808080"
W2K_LIGHT    = "#ffffff"
W2K_FACE     = "#d4d0c8"
W2K_TEXT     = "#000000"
W2K_TITLE_BG = "#000080"
W2K_TITLE_FG = "#ffffff"
W2K_ENTRY    = "#ffffff"
W2K_SEL_BG   = "#000080"
W2K_SEL_FG   = "#ffffff"

# All fonts doubled (8→16, 7→14)
W2K_FONT    = ("Tahoma", 16)
W2K_FONT_B  = ("Tahoma", 16, "bold")
W2K_FONT_SM = ("Tahoma", 14)


class Win2KButton(tk.Canvas):
    """Pixel-accurate Windows 2000 raised button — text size ×2."""

    FACE   = "#d4d0c8"
    HI_OUT = "#ffffff"
    HI_IN  = "#e0ddd6"
    SH_IN  = "#808080"
    SH_OUT = "#404040"
    TEXT_N = "#000000"
    TEXT_D = "#808080"
    TEXT_S = "#ffffff"

    def __init__(self, parent, text="", command=None,
                 width=None, padx=16, pady=6,
                 font=None, default="normal", state="normal"):
        self._font_spec = font or W2K_FONT
        self._text      = text
        self._command   = command
        self._state     = state
        self._default   = default
        self._pressed   = False
        self._inside    = False

        tmp = tk.Label(parent, text=text, font=self._font_spec)
        tmp.update_idletasks()
        tw = tmp.winfo_reqwidth()
        th = tmp.winfo_reqheight()
        tmp.destroy()

        if width is not None:
            tmp2 = tk.Label(parent, text="W" * width, font=self._font_spec)
            tmp2.update_idletasks()
            tw = max(tw, tmp2.winfo_reqwidth())
            tmp2.destroy()

        self._bw = tw + 2 * padx + 4
        self._bh = th + 2 * pady + 4

        super().__init__(parent,
                         width=self._bw, height=self._bh,
                         bd=0, highlightthickness=0, cursor="arrow")
        self._render()
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)

    def _render(self, pressed=False):
        self.delete("all")
        w, h = self._bw - 1, self._bh - 1

        hi_out = self.SH_OUT if pressed else self.HI_OUT
        hi_in  = self.SH_IN  if pressed else self.HI_IN
        sh_in  = self.HI_IN  if pressed else self.SH_IN
        sh_out = self.HI_OUT if pressed else self.SH_OUT

        self.create_rectangle(2, 2, w - 1, h - 1, fill=self.FACE, outline="")

        self.create_line(0, 0, w,     0,     fill=hi_out)
        self.create_line(0, 0, 0,     h,     fill=hi_out)
        self.create_line(0, h, w + 1, h,     fill=sh_out)
        self.create_line(w, 0, w,     h,     fill=sh_out)

        self.create_line(1, 1, w - 1,     1,     fill=hi_in)
        self.create_line(1, 1, 1,         h - 1, fill=hi_in)
        self.create_line(1, h - 1, w - 1, h - 1, fill=sh_in)
        self.create_line(w - 1, 1, w - 1, h - 1, fill=sh_in)

        if self._default == "active" and not pressed:
            self.create_rectangle(0, 0, w, h, outline="#000000", fill="")

        ox = 1 if pressed else 0
        cx, cy = self._bw // 2 + ox, self._bh // 2 + ox

        if self._state == "disabled":
            self.create_text(cx + 1, cy + 1, text=self._text,
                             font=self._font_spec, fill=self.TEXT_S)
            self.create_text(cx, cy, text=self._text,
                             font=self._font_spec, fill=self.TEXT_D)
        else:
            self.create_text(cx, cy, text=self._text,
                             font=self._font_spec, fill=self.TEXT_N)

    def config(self, **kw):
        for key in ("state", "default", "text"):
            if key in kw:
                setattr(self, f"_{key}", kw[key])
        if "font" in kw:
            self._font_spec = kw["font"]
        if kw:
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


def w2k_btn(parent, text, command, width=None, font=None,
            default="normal", padx=16, pady=6):
    return Win2KButton(parent, text=text, command=command,
                       width=width, font=font, default=default,
                       padx=padx, pady=pady)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Shorts → GIF Converter")
        self.resizable(False, False)
        self.configure(bg=W2K_BG)
        self._apply_w2k_style()
        self._build_ui()
        self._check_clipboard_on_focus()

    def _apply_w2k_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TProgressbar",
                        troughcolor="#c0c0c0",
                        background=W2K_TITLE_BG,
                        borderwidth=2,
                        relief="sunken")
        style.configure("TCombobox",
                        fieldbackground=W2K_ENTRY,
                        background=W2K_FACE,
                        foreground=W2K_TEXT,
                        selectbackground=W2K_SEL_BG,
                        selectforeground=W2K_SEL_FG,
                        arrowcolor=W2K_TEXT)
        self.option_add("*TCombobox*Listbox.background",       W2K_ENTRY)
        self.option_add("*TCombobox*Listbox.foreground",       W2K_TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", W2K_SEL_BG)
        self.option_add("*TCombobox*Listbox.selectForeground", W2K_SEL_FG)
        self.option_add("*TCombobox*Listbox.font",             W2K_FONT)

    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=W2K_TITLE_BG, height=36)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(title_bar,
                 text="  YouTube Shorts → GIF Converter",
                 font=W2K_FONT_B,
                 bg=W2K_TITLE_BG, fg=W2K_TITLE_FG,
                 anchor="w").pack(side="left", fill="y")

        for sym, cmd in [("_", self.iconify), ("X", self.destroy)]:
            Win2KButton(title_bar, text=sym, command=cmd,
                        font=W2K_FONT_B, padx=10, pady=2
                        ).pack(side="right", padx=1, pady=2)

        # ── Body ───────────────────────────────────────────────────────
        body = tk.Frame(self, bg=W2K_BG, padx=14, pady=12)
        body.pack(fill="both")

        # URL group
        url_lf = tk.LabelFrame(body, text="YouTube URL",
                                font=W2K_FONT, bg=W2K_BG, fg=W2K_TEXT,
                                relief="groove", bd=2)
        url_lf.pack(fill="x", pady=(0, 10))

        url_inner = tk.Frame(url_lf, bg=W2K_BG)
        url_inner.pack(fill="x", padx=8, pady=6)

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(url_inner,
                                   textvariable=self.url_var,
                                   font=W2K_FONT,
                                   bg=W2K_ENTRY, fg=W2K_TEXT,
                                   insertbackground=W2K_TEXT,
                                   relief="sunken", bd=2, width=38)
        self.url_entry.pack(side="left", fill="x", expand=True)
        w2k_btn(url_inner, "붙여넣기(&P)", self._paste_url,
                width=10, padx=14).pack(side="left", padx=(6, 0))

        # Options group
        opt_lf = tk.LabelFrame(body, text="변환 옵션",
                                font=W2K_FONT, bg=W2K_BG, fg=W2K_TEXT,
                                relief="groove", bd=2)
        opt_lf.pack(fill="x", pady=(0, 10))

        opt_inner = tk.Frame(opt_lf, bg=W2K_BG)
        opt_inner.pack(padx=10, pady=8, fill="x")

        # FPS
        tk.Label(opt_inner, text="FPS:", font=W2K_FONT,
                 bg=W2K_BG, fg=W2K_TEXT).grid(row=0, column=0, sticky="w")
        self.fps_var = tk.IntVar(value=15)
        tk.Spinbox(opt_inner, from_=5, to=30, increment=5,
                   textvariable=self.fps_var,
                   width=4, font=W2K_FONT,
                   bg=W2K_ENTRY, fg=W2K_TEXT,
                   relief="sunken", bd=2,
                   buttonbackground=W2K_FACE
                   ).grid(row=0, column=1, padx=(6, 20), sticky="w")

        # Scale
        tk.Label(opt_inner, text="가로 크기(px):", font=W2K_FONT,
                 bg=W2K_BG, fg=W2K_TEXT).grid(row=0, column=2, sticky="w")
        self.scale_var = tk.IntVar(value=480)
        ttk.Combobox(opt_inner, textvariable=self.scale_var,
                     values=[240, 320, 480, 640, 720],
                     width=6, state="readonly",
                     font=W2K_FONT
                     ).grid(row=0, column=3, padx=(6, 20), sticky="w")

        # Output dir
        tk.Label(opt_inner, text="저장 위치:", font=W2K_FONT,
                 bg=W2K_BG, fg=W2K_TEXT).grid(row=0, column=4, sticky="w")
        self.outdir_var = tk.StringVar(value=OUTPUT_DIR)
        tk.Entry(opt_inner, textvariable=self.outdir_var,
                 font=W2K_FONT_SM, bg=W2K_ENTRY, fg=W2K_TEXT,
                 relief="sunken", bd=2, width=18,
                 state="readonly"
                 ).grid(row=0, column=5, padx=(6, 6), sticky="w")
        w2k_btn(opt_inner, "찾아보기...", self._choose_dir,
                width=8, padx=12).grid(row=0, column=6)

        # ── Separator ──────────────────────────────────────────────────
        sep_outer = tk.Frame(body, bg=W2K_DARK, height=2)
        sep_outer.pack(fill="x", pady=6)
        tk.Frame(sep_outer, bg=W2K_LIGHT, height=1).pack(fill="x", pady=(1, 0))

        # ── Convert button row ─────────────────────────────────────────
        btn_row = tk.Frame(body, bg=W2K_BG)
        btn_row.pack(pady=6)

        self.convert_btn = w2k_btn(btn_row, "GIF 변환 시작(&C)",
                                    self._start_conversion,
                                    width=18, font=W2K_FONT_B,
                                    default="active", pady=8)
        self.convert_btn.pack(side="left", padx=4)

        w2k_btn(btn_row, "닫기(&X)", self.destroy,
                width=10, pady=8).pack(side="left", padx=4)

        # ── Status group ───────────────────────────────────────────────
        status_lf = tk.LabelFrame(body, text="상태",
                                   font=W2K_FONT, bg=W2K_BG, fg=W2K_TEXT,
                                   relief="groove", bd=2)
        status_lf.pack(fill="x", pady=(8, 0))

        status_inner = tk.Frame(status_lf, bg=W2K_BG)
        status_inner.pack(fill="x", padx=8, pady=6)

        self.progress_lbl = tk.Label(status_inner, text="대기 중...",
                                      font=W2K_FONT, bg=W2K_BG, fg=W2K_TEXT,
                                      anchor="w")
        self.progress_lbl.pack(fill="x")

        self.progress = ttk.Progressbar(status_inner,
                                         mode="indeterminate", length=600)
        self.progress.pack(fill="x", pady=(4, 0))

        # ── Result row ─────────────────────────────────────────────────
        self.result_frame = tk.Frame(body, bg=W2K_BG)
        self.result_frame.pack(fill="x", pady=(6, 4))

        result_box = tk.Frame(self.result_frame,
                               bg=W2K_ENTRY, relief="sunken", bd=2)
        result_box.pack(side="left", fill="x", expand=True)
        self.result_lbl = tk.Label(result_box, text="",
                                    font=W2K_FONT_SM,
                                    bg=W2K_ENTRY, fg=W2K_TEXT,
                                    wraplength=560, justify="left", anchor="w",
                                    padx=6, pady=4)
        self.result_lbl.pack(fill="x")

        self.open_btn = w2k_btn(self.result_frame, "폴더 열기",
                                 self._open_in_finder, width=10)
        self._last_gif = None

    # ── Events ─────────────────────────────────────────────────────────────────
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
        self.after(0, lambda: self.progress_lbl.config(text=msg))

    def _on_done(self, gif_path):
        self._last_gif = gif_path
        size_mb = os.path.getsize(gif_path) / 1024 / 1024
        self.after(0, lambda: self._finish(
            f"저장 완료: {gif_path}\n({size_mb:.1f} MB)", success=True))

    def _on_error(self, msg):
        self.after(0, lambda: self._finish(msg, success=False))

    def _finish(self, msg, success):
        self.progress.stop()
        self.convert_btn.config(state="normal")
        color = "#000080" if success else "#800000"
        self.progress_lbl.config(text="완료!" if success else "오류 발생")
        self.result_lbl.config(text=msg, fg=color)
        if success and self._last_gif:
            self.open_btn.pack(side="right", padx=(6, 0))

    def _open_in_finder(self):
        if self._last_gif and os.path.exists(self._last_gif):
            subprocess.run(["open", "-R", self._last_gif])


if __name__ == "__main__":
    app = App()
    app.mainloop()
