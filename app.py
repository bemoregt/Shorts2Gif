import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import os
import re
import tempfile
import shutil
import math

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


# ── macOS X Aqua Design System ─────────────────────────────────────────────────
AQ_BG      = "#ececec"   # window content background
AQ_CARD    = "#f7f7f7"   # groupbox / card background
AQ_TB_TOP  = "#d8d8d8"   # title bar gradient top
AQ_TB_BOT  = "#a8a8a8"   # title bar gradient bottom
AQ_TB_LINE = "#808080"   # title bar bottom separator
AQ_BLUE_T  = "#5ab0f8"   # default button gradient top
AQ_BLUE_B  = "#1060d8"   # default button gradient bottom
AQ_BLUE_BD = "#0850b8"   # default button border
AQ_BTN_T   = "#f4f4f4"   # normal button gradient top
AQ_BTN_B   = "#cccccc"   # normal button gradient bottom
AQ_BTN_BD  = "#999999"   # normal button border
AQ_TEXT    = "#1a1a1a"
AQ_TEXT_S  = "#6d6d72"
AQ_ENTRY   = "#ffffff"
AQ_SEP     = "#c0c0c0"
AQ_FOCUS   = "#5ab0f8"

AQ_RED     = "#ff5f57"   # traffic light — close
AQ_YELLOW  = "#febc2e"   # traffic light — minimize
AQ_GREEN   = "#28c840"   # traffic light — zoom

AQ_FONT      = ("Lucida Grande", 12)
AQ_FONT_B    = ("Lucida Grande", 12, "bold")
AQ_FONT_SM   = ("Lucida Grande", 11)
AQ_FONT_TITLE = ("Lucida Grande", 13)
AQ_FONT_CAP  = ("Lucida Grande", 10)


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


class AquaButton(tk.Canvas):
    """macOS Aqua pill-shaped gradient button."""

    def __init__(self, parent, text="", command=None,
                 default=False, min_width=80, padx=18, pady=6,
                 font=None, bg=None):
        self._text    = text
        self._command = command
        self._default = default   # True → blue button
        self._state   = "normal"
        self._pressed = False
        self._inside  = False
        self._font    = font or AQ_FONT
        self._cbg     = bg or AQ_BG

        tmp = tk.Label(parent, text=text, font=self._font)
        tmp.update_idletasks()
        tw = max(tmp.winfo_reqwidth(), min_width - 2 * padx)
        th = tmp.winfo_reqheight()
        tmp.destroy()

        self._bw = tw + 2 * padx
        self._bh = th + 2 * pady
        self._r  = self._bh // 2   # pill radius

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
        r = min(self._r, h // 2)

        if self._default:
            top_c, bot_c, bdr_c = AQ_BLUE_T, AQ_BLUE_B, AQ_BLUE_BD
            txt_c = "#ffffff"
        else:
            top_c, bot_c, bdr_c = AQ_BTN_T, AQ_BTN_B, AQ_BTN_BD
            txt_c = AQ_TEXT

        if pressed:
            top_c = lerp_color(top_c, "#000000", 0.12)
            bot_c = lerp_color(bot_c, "#000000", 0.12)
        if self._state == "disabled":
            top_c = lerp_color(top_c, AQ_BG, 0.45)
            bot_c = lerp_color(bot_c, AQ_BG, 0.45)
            txt_c = AQ_TEXT_S

        # Gradient fill clipped to pill shape
        for y in range(h):
            t = y / max(h - 1, 1)
            color = lerp_color(top_c, bot_c, t)
            if y < r:
                dx = int(r - math.sqrt(max(0.0, r*r - (r - y - 0.5)**2)))
            elif y > h - r - 1:
                ri = h - 1 - y
                dx = int(r - math.sqrt(max(0.0, r*r - (r - ri - 0.5)**2)))
            else:
                dx = 0
            if dx < w:
                self.create_line(dx, y, w - dx, y, fill=color)

        # Pill border
        self._pill_border(0, 0, w - 1, h - 1, r, bdr_c)

        # Inner highlight on top edge (Aqua gloss line)
        if not pressed and not self._state == "disabled":
            hi = lerp_color(top_c, "#ffffff", 0.55)
            if 1 < r:
                dx1 = int(r - math.sqrt(max(0.0, r*r - (r - 1.5)**2)))
                self.create_line(dx1, 1, w - dx1, 1, fill=hi)

        # Label
        ox = 1 if pressed else 0
        self.create_text(w // 2 + ox, h // 2 + ox,
                         text=self._text, font=self._font, fill=txt_c)

    def _pill_border(self, x1, y1, x2, y2, r, color):
        self.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90, style="arc", outline=color)
        self.create_arc(x2-2*r,  y1,      x2,     y1+2*r, start=0,   extent=90, style="arc", outline=color)
        self.create_arc(x1,      y2-2*r,  x1+2*r, y2,     start=180, extent=90, style="arc", outline=color)
        self.create_arc(x2-2*r,  y2-2*r,  x2,     y2,     start=270, extent=90, style="arc", outline=color)
        self.create_line(x1+r, y1, x2-r, y1, fill=color)
        self.create_line(x1+r, y2, x2-r, y2, fill=color)
        self.create_line(x1, y1+r, x1, y2-r, fill=color)
        self.create_line(x2, y1+r, x2, y2-r, fill=color)

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
        self.configure(bg=AQ_BG)
        self.overrideredirect(True)
        self._drag_x = self._drag_y = 0
        self._apply_style()
        self._build_ui()
        self._check_clipboard_on_focus()
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - self.winfo_reqwidth()) // 2}"
                      f"+{(sh - self.winfo_reqheight()) // 2}")

    # ── Style ──────────────────────────────────────────────────────────────────
    def _apply_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Aqua.Horizontal.TProgressbar",
                        troughcolor="#d0d0d8",
                        background=AQ_FOCUS,
                        borderwidth=0,
                        thickness=8)
        style.configure("TCombobox",
                        fieldbackground=AQ_ENTRY,
                        background=AQ_CARD,
                        foreground=AQ_TEXT,
                        selectbackground=AQ_FOCUS,
                        selectforeground="#ffffff",
                        borderwidth=1)
        self.option_add("*TCombobox*Listbox.background",       AQ_ENTRY)
        self.option_add("*TCombobox*Listbox.foreground",       AQ_TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", AQ_FOCUS)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font",             AQ_FONT)

    # ── Title bar ──────────────────────────────────────────────────────────────
    def _build_title_bar(self, parent):
        tb = tk.Canvas(parent, height=28, bd=0, highlightthickness=0,
                       bg=AQ_TB_BOT)
        tb.pack(fill="x")
        self._tb = tb

        # Traffic-light ovals (drawn as canvas items; always above gradient)
        lights = [
            (AQ_RED,    lerp_color(AQ_RED,    "#000000", 0.18), self.destroy),
            (AQ_YELLOW, lerp_color(AQ_YELLOW, "#000000", 0.18), self.iconify),
            (AQ_GREEN,  lerp_color(AQ_GREEN,  "#000000", 0.18), lambda: None),
        ]
        self._light_ids = []
        for i, (fill, outline, cmd) in enumerate(lights):
            x0 = 10 + i * 18
            oid = tb.create_oval(x0, 8, x0 + 12, 20,
                                 fill=fill, outline=outline, tags="lights")
            tb.tag_bind(oid, "<Button-1>", lambda e, c=cmd: c())
            self._light_ids.append(oid)

        def draw(event=None):
            tb.delete("tbbg")
            w = tb.winfo_width() or 540
            for y in range(28):
                tb.create_line(0, y, w, y,
                               fill=lerp_color(AQ_TB_TOP, AQ_TB_BOT, y / 27),
                               tags="tbbg")
            tb.create_line(0, 27, w, 27, fill=AQ_TB_LINE, tags="tbbg")
            tb.create_text(w // 2, 13,
                           text="YouTube  →  GIF  Converter",
                           font=AQ_FONT_TITLE, fill="#333333", tags="tbbg")
            tb.tag_lower("tbbg")   # keep gradient below traffic lights

        tb.bind("<Configure>", draw)
        self.after(10, draw)

        # Drag on title bar background
        tb.bind("<ButtonPress-1>",  self._drag_start)
        tb.bind("<B1-Motion>",      self._drag_move)

    # ── Group box ──────────────────────────────────────────────────────────────
    def _group(self, parent, title=""):
        """macOS HIG–style group box: small label + white card."""
        outer = tk.Frame(parent, bg=AQ_BG)
        outer.pack(fill="x", padx=14, pady=(0, 10))
        if title:
            tk.Label(outer, text=title,
                     font=AQ_FONT_CAP, bg=AQ_BG, fg=AQ_TEXT_S,
                     anchor="w").pack(fill="x", pady=(0, 3))
        card = tk.Frame(outer, bg=AQ_CARD,
                        highlightbackground=AQ_SEP,
                        highlightthickness=1)
        card.pack(fill="x")
        inner = tk.Frame(card, bg=AQ_CARD, padx=12, pady=10)
        inner.pack(fill="x")
        return inner

    # ── Entry helper ───────────────────────────────────────────────────────────
    def _entry(self, parent, var, width, state="normal", small=False):
        return tk.Entry(parent,
                        textvariable=var,
                        font=AQ_FONT_SM if small else AQ_FONT,
                        bg=AQ_ENTRY, fg=AQ_TEXT,
                        insertbackground=AQ_TEXT,
                        disabledbackground=AQ_CARD,
                        disabledforeground=AQ_TEXT_S,
                        relief="sunken", bd=2,
                        highlightcolor=AQ_FOCUS,
                        highlightthickness=0,
                        width=width, state=state)

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_title_bar(self)

        # Window body border
        tk.Frame(self, bg=AQ_SEP, height=1).pack(fill="x")

        body = tk.Frame(self, bg=AQ_BG)
        body.pack(fill="both", pady=10)

        # ── URL group ──────────────────────────────────────────────────
        url_inner = self._group(body, "YouTube URL")

        url_row = tk.Frame(url_inner, bg=AQ_CARD)
        url_row.pack(fill="x")

        self.url_var = tk.StringVar()
        self.url_entry = self._entry(url_row, self.url_var, width=40)
        self.url_entry.pack(side="left", fill="x", expand=True)

        AquaButton(url_row, "붙여넣기", self._paste_url,
                   min_width=80, padx=12, pady=4,
                   font=AQ_FONT_SM, bg=AQ_CARD
                   ).pack(side="left", padx=(6, 0))

        # ── Options group ──────────────────────────────────────────────
        opt_inner = self._group(body, "변환 옵션")

        row1 = tk.Frame(opt_inner, bg=AQ_CARD)
        row1.pack(fill="x")

        # FPS
        tk.Label(row1, text="FPS", font=AQ_FONT,
                 bg=AQ_CARD, fg=AQ_TEXT,
                 width=10, anchor="w").pack(side="left")
        self.fps_var = tk.IntVar(value=15)
        tk.Spinbox(row1, from_=5, to=30, increment=5,
                   textvariable=self.fps_var,
                   width=4, font=AQ_FONT,
                   bg=AQ_ENTRY, fg=AQ_TEXT,
                   buttonbackground=AQ_CARD,
                   relief="sunken", bd=2
                   ).pack(side="left", padx=(0, 20))

        # Scale
        tk.Label(row1, text="가로 크기", font=AQ_FONT,
                 bg=AQ_CARD, fg=AQ_TEXT).pack(side="left")
        self.scale_var = tk.IntVar(value=480)
        ttk.Combobox(row1, textvariable=self.scale_var,
                     values=[240, 320, 480, 640, 720],
                     width=7, state="readonly",
                     font=AQ_FONT).pack(side="left", padx=(6, 0))

        # Separator
        tk.Frame(opt_inner, bg=AQ_SEP, height=1).pack(fill="x", pady=8)

        row2 = tk.Frame(opt_inner, bg=AQ_CARD)
        row2.pack(fill="x")

        tk.Label(row2, text="저장 위치", font=AQ_FONT,
                 bg=AQ_CARD, fg=AQ_TEXT,
                 width=10, anchor="w").pack(side="left")
        self.outdir_var = tk.StringVar(value=OUTPUT_DIR)
        self._entry(row2, self.outdir_var, width=28,
                    state="readonly", small=True
                    ).pack(side="left", fill="x", expand=True)
        AquaButton(row2, "찾기", self._choose_dir,
                   min_width=60, padx=12, pady=4,
                   font=AQ_FONT_SM, bg=AQ_CARD
                   ).pack(side="right", padx=(6, 0))

        # ── Divider ────────────────────────────────────────────────────
        tk.Frame(body, bg=AQ_SEP, height=1).pack(fill="x", padx=14, pady=(0, 10))

        # ── Action buttons ─────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=AQ_BG)
        btn_row.pack(pady=(0, 10))

        AquaButton(btn_row, "닫기", self.destroy,
                   min_width=80, padx=16, pady=7,
                   font=AQ_FONT).pack(side="left", padx=4)

        self.convert_btn = AquaButton(btn_row, "GIF 변환 시작",
                                       self._start_conversion,
                                       default=True,
                                       min_width=200, padx=22, pady=7,
                                       font=AQ_FONT_B)
        self.convert_btn.pack(side="left", padx=4)

        # ── Status group ───────────────────────────────────────────────
        status_inner = self._group(body, "상태")

        self.progress_lbl = tk.Label(status_inner, text="대기 중...",
                                      font=AQ_FONT, bg=AQ_CARD, fg=AQ_TEXT_S,
                                      anchor="w")
        self.progress_lbl.pack(fill="x")

        self.progress = ttk.Progressbar(status_inner, mode="indeterminate",
                                         length=460,
                                         style="Aqua.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(6, 0))

        # ── Result ─────────────────────────────────────────────────────
        self.result_frame = tk.Frame(body, bg=AQ_BG)
        self.result_frame.pack(fill="x", padx=14, pady=(0, 6))

        self.result_lbl = tk.Label(self.result_frame, text="",
                                    font=AQ_FONT_SM, bg=AQ_BG, fg=AQ_TEXT,
                                    wraplength=420, justify="left", anchor="w")
        self.result_lbl.pack(side="left", fill="x", expand=True)

        self.open_btn = AquaButton(self.result_frame, "Finder 열기",
                                    self._open_in_finder,
                                    min_width=100, padx=14, pady=6,
                                    font=AQ_FONT_SM)
        self._last_gif = None

    # ── Drag ───────────────────────────────────────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

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
        self.after(0, lambda: self.progress_lbl.config(text=msg, fg=AQ_TEXT_S))

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
            fg=AQ_FOCUS if success else "#cc2222")
        self.result_lbl.config(
            text=msg,
            fg=AQ_TEXT if success else "#cc2222")
        if success and self._last_gif:
            self.open_btn.pack(side="right", padx=(8, 0))

    def _open_in_finder(self):
        if self._last_gif and os.path.exists(self._last_gif):
            subprocess.run(["open", "-R", self._last_gif])


if __name__ == "__main__":
    app = App()
    app.mainloop()
