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


# ── SGI IRIX 4Dwm Indigo Magic Design System ──────────────────────────────────
#  Reference: Silicon Graphics IRIX 5.x / 6.x Indigo Magic desktop
#  Characteristic blue-gray window body, deep indigo title bar, SGI teal accent.

IDM_WIN_BG  = "#9090a8"   # window / panel body (blue-gray)
IDM_BODY    = "#a0a0b8"   # slightly lighter body area
IDM_HI1     = "#d0d0e8"   # bevel highlight outer
IDM_HI2     = "#b8b8d0"   # bevel highlight inner
IDM_SH1     = "#505068"   # bevel shadow inner
IDM_SH2     = "#303050"   # bevel shadow outer
IDM_TB_TOP  = "#6060c0"   # indigo title bar gradient top
IDM_TB_BOT  = "#20205a"   # indigo title bar gradient bottom
IDM_TB_FG   = "#ffffff"
IDM_TEAL    = "#20d8d8"   # SGI teal / cyan — accent & active highlight
IDM_TEAL_D  = "#009898"   # darker teal for borders
IDM_BTN     = "#a0a0bc"   # button face (blue-tinted gray)
IDM_BTN_HI  = "#d0d0e4"   # button bevel highlight
IDM_BTN_SH  = "#484860"   # button bevel shadow
IDM_BTN_P   = "#808098"   # pressed button face
IDM_TEXT    = "#000000"
IDM_TEXT_W  = "#ffffff"
IDM_TEXT_D  = "#606080"   # dimmed text
IDM_ENTRY   = "#e8e8f8"   # entry field (pale blue-white)
IDM_SEP     = "#606080"
IDM_SHELF   = "#303050"   # SGI shelf bar (bottom strip)

IDM_FONT    = ("Helvetica", 12)
IDM_FONT_B  = ("Helvetica", 12, "bold")
IDM_FONT_SM = ("Helvetica", 10)
IDM_FONT_T  = ("Helvetica", 13, "bold")
IDM_FONT_CAP = ("Helvetica", 9, "bold")


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def bevel_rect(canvas, x1, y1, x2, y2, depth=2, raised=True, bg=None):
    """Draw a Motif-style 3-D bevel rectangle on a Canvas."""
    face = bg or IDM_BTN
    hi   = IDM_BTN_HI if raised else IDM_BTN_SH
    sh   = IDM_BTN_SH if raised else IDM_BTN_HI
    # Face
    canvas.create_rectangle(x1 + depth, y1 + depth,
                             x2 - depth, y2 - depth,
                             fill=face, outline="")
    for i in range(depth):
        t = i / depth
        c_hi = lerp_color(hi, face, t * 0.5)
        c_sh = lerp_color(sh, face, t * 0.5)
        canvas.create_line(x1+i, y1+i, x2-i,   y1+i,   fill=c_hi)  # top
        canvas.create_line(x1+i, y1+i, x1+i,   y2-i,   fill=c_hi)  # left
        canvas.create_line(x1+i, y2-i, x2-i+1, y2-i,   fill=c_sh)  # bottom
        canvas.create_line(x2-i, y1+i, x2-i,   y2-i+1, fill=c_sh)  # right


class MotifButton(tk.Canvas):
    """SGI 4Dwm Motif-style 3-D beveled button."""

    def __init__(self, parent, text="", command=None,
                 min_width=60, padx=14, pady=5,
                 font=None, color=None, bg=None, depth=2):
        self._text   = text
        self._command = command
        self._state  = "normal"
        self._color  = color
        self._pressed = False
        self._inside  = False
        self._font   = font or IDM_FONT
        self._cbg    = bg or IDM_WIN_BG
        self._depth  = depth

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
        d = self._depth
        face = IDM_BTN_P if pressed else IDM_BTN
        bevel_rect(self, 0, 0, w - 1, h - 1,
                   depth=d, raised=not pressed, bg=face)
        tc = IDM_TEXT_D if self._state == "disabled" \
             else (self._color or IDM_TEXT)
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
        self.configure(bg=IDM_SH2)
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

    # ── ttk style ──────────────────────────────────────────────────────────────
    def _apply_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("IDM.Horizontal.TProgressbar",
                        troughcolor=IDM_SH2,
                        background=IDM_TEAL,
                        borderwidth=1,
                        thickness=10)
        style.configure("TCombobox",
                        fieldbackground=IDM_ENTRY,
                        background=IDM_BTN,
                        foreground=IDM_TEXT,
                        selectbackground=IDM_TEAL,
                        selectforeground="#000000",
                        borderwidth=1)
        self.option_add("*TCombobox*Listbox.background",       IDM_ENTRY)
        self.option_add("*TCombobox*Listbox.foreground",       IDM_TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", IDM_TEAL)
        self.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        self.option_add("*TCombobox*Listbox.font",             IDM_FONT)

    # ── Title bar ──────────────────────────────────────────────────────────────
    def _build_title_bar(self, parent):
        tb = tk.Canvas(parent, height=26, bd=0, highlightthickness=0,
                       bg=IDM_TB_BOT)
        tb.pack(fill="x")
        self._tb = tb

        # Window-menu square (left)
        wm = tb.create_rectangle(4, 4, 20, 22,
                                  fill=IDM_BTN, outline=IDM_BTN_SH, tags="tbctrl")
        tb.create_text(12, 13, text="▤", font=("Helvetica", 8),
                       fill=IDM_TEXT, tags="tbctrl")

        # Right-side control buttons: minimize, maximize, close
        ctrl_specs = [
            (None,        self.iconify,  "_"),
            (None,        lambda: None, "□"),
            (IDM_TEAL,    self.destroy,  "×"),
        ]
        self._tb_btns = []
        for i, (accent, cmd, sym) in enumerate(ctrl_specs):
            rx1 = self._tb_btn_x(i)
            face = accent if accent else IDM_BTN
            rid = tb.create_rectangle(rx1, 4, rx1 + 18, 22,
                                       fill=face, outline=IDM_BTN_SH,
                                       tags="tbctrl")
            tid = tb.create_text(rx1 + 9, 13, text=sym,
                                  font=IDM_FONT_SM,
                                  fill=IDM_TEXT_W if accent else IDM_TEXT,
                                  tags="tbctrl")
            for item in (rid, tid):
                tb.tag_bind(item, "<Button-1>", lambda e, c=cmd: c())
            self._tb_btns.append((rid, tid))

        def draw(event=None):
            tb.delete("tbbg")
            w = tb.winfo_width() or 560
            # Indigo gradient
            for y in range(26):
                tb.create_line(0, y, w, y,
                               fill=lerp_color(IDM_TB_TOP, IDM_TB_BOT, y / 25),
                               tags="tbbg")
            # Teal accent stripe at top
            tb.create_line(0, 0, w, 0, fill=IDM_TEAL,   tags="tbbg")
            tb.create_line(0, 1, w, 1, fill=IDM_TEAL_D, tags="tbbg")
            # Bottom separator
            tb.create_line(0, 25, w, 25, fill=IDM_SH2, tags="tbbg")
            # Title
            tb.create_text(w // 2, 13,
                           text="YouTube  →  GIF  Converter",
                           font=IDM_FONT_T, fill=IDM_TB_FG, tags="tbbg")
            tb.tag_lower("tbbg")
            # Re-position right-side buttons after resize
            for i, (rid, tid) in enumerate(self._tb_btns):
                rx1 = self._tb_btn_x(i, w)
                tb.coords(rid, rx1, 4, rx1 + 18, 22)
                tb.coords(tid, rx1 + 9, 13)

        tb.bind("<Configure>", draw)
        self.after(10, draw)
        tb.bind("<ButtonPress-1>", self._drag_start)
        tb.bind("<B1-Motion>",     self._drag_move)

    def _tb_btn_x(self, idx, total_w=None):
        w = total_w or (self._tb.winfo_width() or 560)
        return w - 24 - idx * 22

    # ── Thick window border ────────────────────────────────────────────────────
    def _window_border(self, parent):
        """Draw outer Motif-style thick raised border using nested frames."""
        # Outer shadow (2px)
        f1 = tk.Frame(parent, bg=IDM_HI1, bd=0)
        f1.pack(fill="both", expand=True, padx=0, pady=0)
        f2 = tk.Frame(f1, bg=IDM_HI2, bd=0)
        f2.pack(fill="both", expand=True, padx=1, pady=1)
        f3 = tk.Frame(f2, bg=IDM_SH1, bd=0)
        f3.pack(fill="both", expand=True, padx=1, pady=1)
        f4 = tk.Frame(f3, bg=IDM_SH2, bd=0)
        f4.pack(fill="both", expand=True, padx=1, pady=1)
        inner = tk.Frame(f4, bg=IDM_WIN_BG, bd=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        return inner

    # ── Grooved section frame ──────────────────────────────────────────────────
    def _grooved(self, parent, title=""):
        """Motif-style grooved/etched label frame."""
        outer = tk.Frame(parent, bg=IDM_WIN_BG)
        outer.pack(fill="x", padx=10, pady=(0, 8))

        if title:
            hdr = tk.Frame(outer, bg=IDM_WIN_BG)
            hdr.pack(fill="x", pady=(0, 2))
            # Teal left accent bar
            tk.Frame(hdr, bg=IDM_TEAL, width=4).pack(side="left", fill="y")
            tk.Label(hdr, text=title,
                     font=IDM_FONT_CAP, bg=IDM_WIN_BG, fg=IDM_TEAL,
                     padx=4, pady=1).pack(side="left")
            tk.Frame(hdr, bg=IDM_SEP, height=1).pack(side="left",
                                                       fill="x", expand=True)

        # Grooved box: outer dark, inner light
        groove = tk.Frame(outer,
                          highlightbackground=IDM_SH1,
                          highlightthickness=1)
        groove.pack(fill="x")
        highlight = tk.Frame(groove,
                              highlightbackground=IDM_HI1,
                              highlightthickness=1,
                              bg=IDM_BODY)
        highlight.pack(fill="x", padx=1, pady=1)
        inner = tk.Frame(highlight, bg=IDM_BODY, padx=10, pady=8)
        inner.pack(fill="x")
        return inner

    # ── Entry helper ───────────────────────────────────────────────────────────
    def _entry(self, parent, var, width, state="normal", small=False):
        return tk.Entry(parent,
                        textvariable=var,
                        font=IDM_FONT_SM if small else IDM_FONT,
                        bg=IDM_ENTRY, fg=IDM_TEXT,
                        insertbackground=IDM_TEXT,
                        disabledbackground=IDM_WIN_BG,
                        disabledforeground=IDM_TEXT_D,
                        selectbackground=IDM_TEAL,
                        selectforeground="#000000",
                        relief="sunken", bd=2,
                        width=width, state=state)

    # ── Shelf (SGI bottom toolbar strip) ───────────────────────────────────────
    def _build_shelf(self, parent):
        shelf = tk.Frame(parent, bg=IDM_SHELF, height=22)
        shelf.pack(fill="x", side="bottom")
        shelf.pack_propagate(False)
        # Teal top accent line
        tk.Frame(shelf, bg=IDM_TEAL, height=2).pack(fill="x")
        tk.Label(shelf, text="SGI  IRIX  Indigo Magic",
                 font=IDM_FONT_SM, bg=IDM_SHELF, fg=IDM_TEAL,
                 anchor="w", padx=8).pack(side="left", fill="y")

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_title_bar(self)

        # Thick raised window border wraps all content
        content = self._window_border(self)

        self._build_shelf(content)

        body = tk.Frame(content, bg=IDM_WIN_BG, padx=0, pady=8)
        body.pack(fill="both")

        # ── URL ────────────────────────────────────────────────────────
        url_inner = self._grooved(body, "YOUTUBE URL")

        url_row = tk.Frame(url_inner, bg=IDM_BODY)
        url_row.pack(fill="x")

        self.url_var = tk.StringVar()
        self.url_entry = self._entry(url_row, self.url_var, width=40)
        self.url_entry.pack(side="left", fill="x", expand=True)

        MotifButton(url_row, "붙여넣기", self._paste_url,
                    min_width=80, padx=12, pady=4,
                    font=IDM_FONT_SM, bg=IDM_BODY
                    ).pack(side="left", padx=(6, 0))

        # ── Options ────────────────────────────────────────────────────
        opt_inner = self._grooved(body, "CONVERSION OPTIONS")

        row1 = tk.Frame(opt_inner, bg=IDM_BODY)
        row1.pack(fill="x")

        tk.Label(row1, text="FPS:", font=IDM_FONT,
                 bg=IDM_BODY, fg=IDM_TEXT,
                 width=10, anchor="w").pack(side="left")
        self.fps_var = tk.IntVar(value=15)
        tk.Spinbox(row1, from_=5, to=30, increment=5,
                   textvariable=self.fps_var,
                   width=4, font=IDM_FONT,
                   bg=IDM_ENTRY, fg=IDM_TEXT,
                   buttonbackground=IDM_BTN,
                   selectbackground=IDM_TEAL,
                   relief="sunken", bd=2
                   ).pack(side="left", padx=(0, 20))

        tk.Label(row1, text="가로 크기:", font=IDM_FONT,
                 bg=IDM_BODY, fg=IDM_TEXT).pack(side="left")
        self.scale_var = tk.IntVar(value=480)
        ttk.Combobox(row1, textvariable=self.scale_var,
                     values=[240, 320, 480, 640, 720],
                     width=7, state="readonly",
                     font=IDM_FONT).pack(side="left", padx=(6, 0))

        # Grooved separator
        tk.Frame(opt_inner, bg=IDM_SH1,  height=1).pack(fill="x", pady=(8, 0))
        tk.Frame(opt_inner, bg=IDM_HI1,  height=1).pack(fill="x", pady=(0, 8))

        row2 = tk.Frame(opt_inner, bg=IDM_BODY)
        row2.pack(fill="x")

        tk.Label(row2, text="저장 위치:", font=IDM_FONT,
                 bg=IDM_BODY, fg=IDM_TEXT,
                 width=10, anchor="w").pack(side="left")
        self.outdir_var = tk.StringVar(value=OUTPUT_DIR)
        self._entry(row2, self.outdir_var, width=28,
                    state="readonly", small=True
                    ).pack(side="left", fill="x", expand=True)
        MotifButton(row2, "찾아보기", self._choose_dir,
                    min_width=80, padx=12, pady=4,
                    font=IDM_FONT_SM, bg=IDM_BODY
                    ).pack(side="right", padx=(6, 0))

        # ── Button row ─────────────────────────────────────────────────
        # Etched separator
        tk.Frame(body, bg=IDM_SH1,  height=1).pack(fill="x", padx=10)
        tk.Frame(body, bg=IDM_HI1,  height=1).pack(fill="x", padx=10, pady=(0, 8))

        btn_row = tk.Frame(body, bg=IDM_WIN_BG)
        btn_row.pack(pady=(0, 8))

        self.convert_btn = MotifButton(btn_row, "GIF 변환 시작",
                                        self._start_conversion,
                                        min_width=260, padx=20, pady=8,
                                        font=IDM_FONT_B, color=IDM_TEAL,
                                        depth=3)
        self.convert_btn.pack(side="left", padx=4)

        MotifButton(btn_row, "닫기", self.destroy,
                    min_width=80, padx=16, pady=8,
                    font=IDM_FONT).pack(side="left", padx=4)

        # ── Status ─────────────────────────────────────────────────────
        status_inner = self._grooved(body, "STATUS")

        self.progress_lbl = tk.Label(status_inner, text="대기 중...",
                                      font=IDM_FONT, bg=IDM_BODY,
                                      fg=IDM_TEXT_D, anchor="w")
        self.progress_lbl.pack(fill="x")

        self.progress = ttk.Progressbar(status_inner, mode="indeterminate",
                                         length=460,
                                         style="IDM.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(6, 0))

        # ── Result ─────────────────────────────────────────────────────
        self.result_frame = tk.Frame(body, bg=IDM_WIN_BG)
        self.result_frame.pack(fill="x", padx=10, pady=(0, 4))

        self.result_lbl = tk.Label(self.result_frame, text="",
                                    font=IDM_FONT_SM, bg=IDM_WIN_BG,
                                    fg=IDM_TEXT, wraplength=420,
                                    justify="left", anchor="w")
        self.result_lbl.pack(side="left", fill="x", expand=True)

        self.open_btn = MotifButton(self.result_frame, "Finder 열기",
                                     self._open_in_finder,
                                     min_width=100, padx=14, pady=6,
                                     font=IDM_FONT_SM)
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
        self.after(0, lambda: self.progress_lbl.config(text=msg, fg=IDM_TEXT))

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
            fg=IDM_TEAL if success else "#e04040")
        self.result_lbl.config(
            text=msg,
            fg=IDM_TEXT if success else "#e04040")
        if success and self._last_gif:
            self.open_btn.pack(side="right", padx=(8, 0))

    def _open_in_finder(self):
        if self._last_gif and os.path.exists(self._last_gif):
            subprocess.run(["open", "-R", self._last_gif])


if __name__ == "__main__":
    app = App()
    app.mainloop()
