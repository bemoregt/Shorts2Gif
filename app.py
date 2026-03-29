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


# ── NeXTStep Design System ─────────────────────────────────────────────────────
NS_BG        = "#2d2d2d"   # window background (dark charcoal)
NS_DARKER    = "#1a1a1a"   # title bar / panel headers
NS_PANEL     = "#363636"   # inspector panel body
NS_BTN_FACE  = "#545454"   # button face
NS_BTN_HI    = "#8a8a8a"   # bevel highlight (top-left)
NS_BTN_SH    = "#0f0f0f"   # bevel shadow (bottom-right)
NS_BTN_PRESS = "#3c3c3c"   # pressed face
NS_AMBER     = "#f0c000"   # NeXT amber — close box / accent
NS_TEXT      = "#e8e8e8"   # primary text
NS_TEXT_D    = "#707070"   # dimmed / disabled
NS_ENTRY_BG  = "#d4d4d4"   # entry field (light, high contrast)
NS_ENTRY_FG  = "#000000"
NS_SEP       = "#555555"

NS_FONT      = ("Helvetica", 12)
NS_FONT_B    = ("Helvetica", 12, "bold")
NS_FONT_SM   = ("Helvetica", 10)
NS_FONT_TITLE = ("Helvetica", 13, "bold")
NS_FONT_HDR  = ("Helvetica", 9, "bold")


class NSButton(tk.Canvas):
    """NeXTStep beveled button drawn on a Canvas."""

    def __init__(self, parent, text="", command=None,
                 min_width=60, padx=14, pady=5,
                 font=None, color=None, bg=None):
        self._text    = text
        self._command = command
        self._state   = "normal"
        self._color   = color
        self._pressed = False
        self._inside  = False
        self._font    = font or NS_FONT
        self._cbg     = bg or NS_BG

        tmp = tk.Label(parent, text=text, font=self._font)
        tmp.update_idletasks()
        tw = max(tmp.winfo_reqwidth(), min_width - 2 * padx)
        th = tmp.winfo_reqheight()
        tmp.destroy()

        self._bw = tw + 2 * padx
        self._bh = th + 2 * pady

        super().__init__(parent, width=self._bw, height=self._bh,
                         bd=0, highlightthickness=0, cursor="arrow",
                         bg=self._cbg)
        self._render()
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)

    def _render(self, pressed=False):
        self.delete("all")
        w, h = self._bw, self._bh

        face     = NS_BTN_PRESS if pressed else NS_BTN_FACE
        hi, sh   = (NS_BTN_SH, NS_BTN_HI) if pressed else (NS_BTN_HI, NS_BTN_SH)
        inner_hi = "#3a3a3a" if pressed else "#6a6a6a"
        inner_sh = "#6a6a6a" if pressed else "#2a2a2a"

        # Face
        self.create_rectangle(1, 1, w - 2, h - 2, fill=face, outline="")

        # Outer bevel
        self.create_line(0,   0,   w,     0,   fill=hi)   # top
        self.create_line(0,   0,   0,     h,   fill=hi)   # left
        self.create_line(0,   h-1, w,     h-1, fill=sh)   # bottom
        self.create_line(w-1, 0,   w-1,   h,   fill=sh)   # right

        # Inner bevel (1 px inside)
        self.create_line(1,   1,   w-2,   1,   fill=inner_hi)
        self.create_line(1,   1,   1,     h-2, fill=inner_hi)
        self.create_line(1,   h-2, w-1,   h-2, fill=inner_sh)
        self.create_line(w-2, 1,   w-2,   h-1, fill=inner_sh)

        # Label
        tc = NS_TEXT_D if self._state == "disabled" else (self._color or NS_TEXT)
        ox = 1 if pressed else 0
        self.create_text(w // 2 + ox, h // 2 + ox,
                         text=self._text, font=self._font, fill=tc)

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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube → GIF")
        self.resizable(False, False)
        self.configure(bg=NS_DARKER)
        self.overrideredirect(True)       # custom title bar
        self._drag_x = self._drag_y = 0
        self._apply_style()
        self._build_ui()
        self._check_clipboard_on_focus()
        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = self.winfo_reqwidth()
        h  = self.winfo_reqheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── Style ──────────────────────────────────────────────────────────────────
    def _apply_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("NS.Horizontal.TProgressbar",
                        troughcolor=NS_DARKER,
                        background=NS_AMBER,
                        borderwidth=1,
                        thickness=10)
        style.configure("TCombobox",
                        fieldbackground=NS_ENTRY_BG,
                        background=NS_BTN_FACE,
                        foreground=NS_ENTRY_FG,
                        selectbackground=NS_AMBER,
                        selectforeground=NS_DARKER,
                        borderwidth=1)
        self.option_add("*TCombobox*Listbox.background",       NS_ENTRY_BG)
        self.option_add("*TCombobox*Listbox.foreground",       NS_ENTRY_FG)
        self.option_add("*TCombobox*Listbox.selectBackground", NS_AMBER)
        self.option_add("*TCombobox*Listbox.selectForeground", NS_DARKER)
        self.option_add("*TCombobox*Listbox.font",             NS_FONT)

    # ── Title bar ──────────────────────────────────────────────────────────────
    def _build_title_bar(self, parent):
        bar = tk.Frame(parent, bg=NS_DARKER, height=28)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Amber close box
        close_c = tk.Canvas(bar, width=14, height=14,
                            bg=NS_DARKER, bd=0, highlightthickness=0)
        close_c.create_rectangle(0, 0, 13, 13, fill=NS_AMBER, outline=NS_BTN_SH)
        close_c.pack(side="left", padx=(8, 3), pady=7)
        close_c.bind("<Button-1>", lambda e: self.destroy())

        # Gray miniaturize box
        mini_c = tk.Canvas(bar, width=14, height=14,
                           bg=NS_DARKER, bd=0, highlightthickness=0)
        mini_c.create_rectangle(0, 0, 13, 13, fill=NS_BTN_FACE, outline=NS_BTN_SH)
        mini_c.pack(side="left", padx=(0, 8), pady=7)
        mini_c.bind("<Button-1>", lambda e: self.iconify())

        # 1px separator line (amber stripe)
        tk.Frame(bar, bg=NS_AMBER, width=1).pack(side="left", fill="y", pady=4)

        title_lbl = tk.Label(bar, text="  YouTube  →  GIF  Converter",
                             font=NS_FONT_TITLE, bg=NS_DARKER, fg=NS_TEXT,
                             anchor="w")
        title_lbl.pack(side="left", fill="y")

        # Drag bindings
        for w in (bar, title_lbl):
            w.bind("<ButtonPress-1>",  self._drag_start)
            w.bind("<B1-Motion>",      self._drag_move)

    # ── Inspector panel ────────────────────────────────────────────────────────
    def _panel(self, parent, title):
        """NeXTStep inspector-style panel: dark header + lighter body."""
        wrapper = tk.Frame(parent, bg=NS_BG)
        wrapper.pack(fill="x", padx=10, pady=(0, 8))

        # Header strip
        hdr = tk.Frame(wrapper, bg=NS_DARKER)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title,
                 font=NS_FONT_HDR, bg=NS_DARKER, fg=NS_AMBER,
                 anchor="w", padx=8, pady=3).pack(fill="x")

        # Etched border body
        body = tk.Frame(wrapper, bg=NS_PANEL,
                        highlightbackground=NS_BTN_SH,
                        highlightthickness=1)
        body.pack(fill="x")
        inner = tk.Frame(body, bg=NS_PANEL, padx=10, pady=10)
        inner.pack(fill="x")
        return inner

    # ── Entry helper ───────────────────────────────────────────────────────────
    def _entry(self, parent, textvariable, width, state="normal", small=False):
        font = NS_FONT_SM if small else NS_FONT
        return tk.Entry(parent,
                        textvariable=textvariable,
                        font=font,
                        bg=NS_ENTRY_BG, fg=NS_ENTRY_FG,
                        insertbackground=NS_ENTRY_FG,
                        disabledbackground=NS_PANEL,
                        disabledforeground=NS_TEXT_D,
                        relief="sunken", bd=2,
                        width=width, state=state)

    # ── Separator ──────────────────────────────────────────────────────────────
    def _sep(self, parent):
        tk.Frame(parent, bg=NS_BTN_SH, height=1).pack(fill="x", pady=6)
        tk.Frame(parent, bg=NS_BTN_HI, height=1).pack(fill="x")

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_title_bar(self)

        # Etched window border (1px dark + 1px lighter)
        tk.Frame(self, bg=NS_BTN_SH, height=1).pack(fill="x")
        tk.Frame(self, bg=NS_SEP,    height=1).pack(fill="x")

        body = tk.Frame(self, bg=NS_BG, padx=0, pady=8)
        body.pack(fill="both")

        # ── URL panel ──────────────────────────────────────────────────
        url_inner = self._panel(body, "YOUTUBE URL")

        url_row = tk.Frame(url_inner, bg=NS_PANEL)
        url_row.pack(fill="x")

        self.url_var = tk.StringVar()
        self.url_entry = self._entry(url_row, self.url_var, width=40)
        self.url_entry.pack(side="left", fill="x", expand=True)

        NSButton(url_row, "붙여넣기", self._paste_url,
                 min_width=80, padx=12, pady=4,
                 font=NS_FONT_SM, bg=NS_PANEL
                 ).pack(side="left", padx=(6, 0))

        # ── Options panel ──────────────────────────────────────────────
        opt_inner = self._panel(body, "CONVERSION OPTIONS")

        opt_row = tk.Frame(opt_inner, bg=NS_PANEL)
        opt_row.pack(fill="x")

        # FPS
        tk.Label(opt_row, text="FPS:", font=NS_FONT,
                 bg=NS_PANEL, fg=NS_TEXT,
                 width=10, anchor="w").pack(side="left")
        self.fps_var = tk.IntVar(value=15)
        tk.Spinbox(opt_row, from_=5, to=30, increment=5,
                   textvariable=self.fps_var,
                   width=4, font=NS_FONT,
                   bg=NS_ENTRY_BG, fg=NS_ENTRY_FG,
                   buttonbackground=NS_BTN_FACE,
                   relief="sunken", bd=2
                   ).pack(side="left", padx=(0, 20))

        # Scale
        tk.Label(opt_row, text="가로 크기:", font=NS_FONT,
                 bg=NS_PANEL, fg=NS_TEXT).pack(side="left")
        self.scale_var = tk.IntVar(value=480)
        ttk.Combobox(opt_row, textvariable=self.scale_var,
                     values=[240, 320, 480, 640, 720],
                     width=7, state="readonly",
                     font=NS_FONT).pack(side="left", padx=(6, 0))

        self._sep(opt_inner)

        dir_row = tk.Frame(opt_inner, bg=NS_PANEL)
        dir_row.pack(fill="x")

        tk.Label(dir_row, text="저장 위치:", font=NS_FONT,
                 bg=NS_PANEL, fg=NS_TEXT,
                 width=10, anchor="w").pack(side="left")
        self.outdir_var = tk.StringVar(value=OUTPUT_DIR)
        self._entry(dir_row, self.outdir_var, width=28,
                    state="readonly", small=True
                    ).pack(side="left", fill="x", expand=True)
        NSButton(dir_row, "찾아보기", self._choose_dir,
                 min_width=80, padx=12, pady=4,
                 font=NS_FONT_SM, bg=NS_PANEL
                 ).pack(side="right", padx=(6, 0))

        # ── Convert button row ─────────────────────────────────────────
        tk.Frame(body, bg=NS_BTN_SH, height=1).pack(fill="x", padx=10)
        tk.Frame(body, bg=NS_SEP,    height=1).pack(fill="x", padx=10)

        btn_row = tk.Frame(body, bg=NS_BG)
        btn_row.pack(pady=10)

        self.convert_btn = NSButton(btn_row, "GIF 변환 시작", self._start_conversion,
                                     min_width=280, padx=20, pady=8,
                                     font=NS_FONT_B, color=NS_AMBER)
        self.convert_btn.pack(side="left", padx=4)

        NSButton(btn_row, "닫기", self.destroy,
                 min_width=80, padx=16, pady=8,
                 font=NS_FONT).pack(side="left", padx=4)

        # ── Status panel ───────────────────────────────────────────────
        status_inner = self._panel(body, "STATUS")

        self.progress_lbl = tk.Label(status_inner, text="대기 중...",
                                      font=NS_FONT, bg=NS_PANEL, fg=NS_TEXT_D,
                                      anchor="w")
        self.progress_lbl.pack(fill="x")

        self.progress = ttk.Progressbar(status_inner, mode="indeterminate",
                                         length=460,
                                         style="NS.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(6, 0))

        # ── Result area ────────────────────────────────────────────────
        self.result_frame = tk.Frame(body, bg=NS_BG)
        self.result_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.result_lbl = tk.Label(self.result_frame, text="",
                                    font=NS_FONT_SM, bg=NS_BG, fg=NS_TEXT,
                                    wraplength=420, justify="left", anchor="w")
        self.result_lbl.pack(side="left", fill="x", expand=True)

        self.open_btn = NSButton(self.result_frame, "Finder 열기",
                                  self._open_in_finder,
                                  min_width=100, padx=14, pady=6,
                                  font=NS_FONT_SM)
        self._last_gif = None

    # ── Drag ───────────────────────────────────────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

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
        self.after(0, lambda: self.progress_lbl.config(text=msg, fg=NS_TEXT))

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
            fg=NS_AMBER if success else "#cc4444")
        self.result_lbl.config(
            text=msg,
            fg=NS_TEXT if success else "#cc4444")
        if success and self._last_gif:
            self.open_btn.pack(side="right", padx=(8, 0))

    def _open_in_finder(self):
        if self._last_gif and os.path.exists(self._last_gif):
            subprocess.run(["open", "-R", self._last_gif])


if __name__ == "__main__":
    app = App()
    app.mainloop()
