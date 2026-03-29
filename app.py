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


# ── iOS 6 Skeuomorphism Design System ─────────────────────────────────────────
IOS_BG       = "#efeff4"   # grouped table view background
IOS_CARD     = "#ffffff"   # section card
IOS_NAV_TOP  = "#6d8db5"   # nav bar gradient top
IOS_NAV_BOT  = "#2d527e"   # nav bar gradient bottom
IOS_NAV_FG   = "#ffffff"
IOS_SEP      = "#c8c7cc"   # separator / border
IOS_TEXT     = "#1c1c1e"
IOS_TEXT_SEC = "#8e8e93"

IOS_FONT     = ("Helvetica Neue", 11)
IOS_FONT_B   = ("Helvetica Neue", 12, "bold")
IOS_FONT_SM  = ("Helvetica Neue", 10)
IOS_FONT_NAV = ("Helvetica Neue", 15, "bold")
IOS_FONT_CAP = ("Helvetica Neue", 10)


def lerp_color(c1, c2, t):
    """Linear interpolation between two hex color strings."""
    t = max(0.0, min(1.0, t))
    r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
    g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
    b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


class iOSButton(tk.Canvas):
    """Glossy iOS 6 skeuomorphic button drawn on a Canvas."""
    PALETTES = {
        "blue":  ("#5eb8f8", "#1470d0", "#0d56a8"),
        "green": ("#72d874", "#30b832", "#228020"),
        "gray":  ("#dedee4", "#aeaeb6", "#8e8e96"),
        "red":   ("#ff6868", "#dd2020", "#aa1010"),
    }

    def __init__(self, parent, text="", command=None, color="gray",
                 min_width=80, padx=16, pady=8, font=None, bg=None):
        self._text = text
        self._command = command
        self._color = color
        self._state = "normal"
        self._pressed = False
        self._inside = False
        self._font = font or IOS_FONT
        self._bg = bg or IOS_BG

        tmp = tk.Label(parent, text=text, font=self._font)
        tmp.update_idletasks()
        tw = max(tmp.winfo_reqwidth(), min_width - 2 * padx)
        th = tmp.winfo_reqheight()
        tmp.destroy()

        self._w = tw + 2 * padx
        self._h = th + 2 * pady
        self._r = min(10, self._h // 2)

        super().__init__(parent, width=self._w, height=self._h,
                         bd=0, highlightthickness=0, cursor="arrow",
                         bg=self._bg)
        self._render()
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)

    def _render(self, pressed=False):
        self.delete("all")
        w, h = self._w, self._h
        r = self._r
        top_c, bot_c, border_c = self.PALETTES[self._color]
        text_c = "#ffffff" if self._color in ("blue", "green", "red") else IOS_TEXT

        if pressed:
            top_c = lerp_color(top_c, "#000000", 0.18)
            bot_c = lerp_color(bot_c, "#000000", 0.18)

        if self._state == "disabled":
            top_c = lerp_color(top_c, "#cccccc", 0.55)
            bot_c = lerp_color(bot_c, "#cccccc", 0.55)
            text_c = "#aaaaaa"

        # Two-band iOS gloss gradient: top half is glossy, bottom half is deep
        split = int(h * 0.50)
        gloss_top = lerp_color(top_c, "#ffffff", 0.46)
        gloss_bot = lerp_color(top_c, "#ffffff", 0.12)

        for y in range(h):
            # Clip x bounds to rounded rectangle shape
            if y < r:
                dx = int(r - math.sqrt(max(0.0, r * r - (r - y - 0.5) ** 2)))
            elif y > h - r - 1:
                ri = h - 1 - y
                dx = int(r - math.sqrt(max(0.0, r * r - (r - ri - 0.5) ** 2)))
            else:
                dx = 0

            if y <= split:
                t = y / max(split, 1)
                color = lerp_color(gloss_top, gloss_bot, t)
            else:
                t = (y - split) / max(h - split - 1, 1)
                color = lerp_color(top_c, bot_c, t)

            x1, x2 = dx, w - dx
            if x1 < x2:
                self.create_line(x1, y, x2, y, fill=color)

        # Rounded border
        self._draw_border(0, 0, w - 1, h - 1, r, border_c)

        # Label
        ox = 1 if pressed else 0
        self.create_text(w // 2 + ox, h // 2 + ox + 1,
                         text=self._text, font=self._font, fill=text_c)

    def _draw_border(self, x1, y1, x2, y2, r, color):
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
        self.configure(bg=IOS_BG)
        self._apply_style()
        self._build_ui()
        self._check_clipboard_on_focus()

    def _apply_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("iOS.TProgressbar",
                        troughcolor="#dde0e8",
                        background="#4a90d9",
                        borderwidth=0,
                        thickness=6)
        style.configure("TCombobox",
                        fieldbackground=IOS_CARD,
                        background=IOS_CARD,
                        foreground=IOS_TEXT,
                        selectbackground="#007aff",
                        selectforeground="#ffffff",
                        borderwidth=1)
        self.option_add("*TCombobox*Listbox.background",       IOS_CARD)
        self.option_add("*TCombobox*Listbox.foreground",       IOS_TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", "#007aff")
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font",             IOS_FONT)

    # ── Navigation bar ─────────────────────────────────────────────────────────
    def _build_nav(self):
        nav = tk.Canvas(self, height=44, bd=0, highlightthickness=0,
                        bg=IOS_NAV_BOT)
        nav.pack(fill="x")

        def draw(event=None):
            nav.delete("all")
            w = nav.winfo_width() or 520
            for y in range(44):
                nav.create_line(0, y, w, y,
                                fill=lerp_color(IOS_NAV_TOP, IOS_NAV_BOT, y / 43))
            nav.create_line(0, 0, w, 0,
                            fill=lerp_color(IOS_NAV_TOP, "#ffffff", 0.4))  # top sheen
            nav.create_line(0, 43, w, 43, fill="#1a3560")                  # bottom shadow
            nav.create_text(w // 2, 22, text="YouTube  →  GIF",
                            font=IOS_FONT_NAV, fill=IOS_NAV_FG)

        nav.bind("<Configure>", draw)
        self.after(10, draw)

    # ── Layout helpers ─────────────────────────────────────────────────────────
    def _section_label(self, parent, text):
        tk.Label(parent, text=text.upper(),
                 font=IOS_FONT_CAP, bg=IOS_BG, fg=IOS_TEXT_SEC,
                 anchor="w").pack(fill="x", padx=16, pady=(8, 2))

    def _card(self, parent):
        return tk.Frame(parent, bg=IOS_CARD,
                        highlightbackground=IOS_SEP,
                        highlightthickness=1)

    def _row_sep(self, card):
        tk.Frame(card, bg=IOS_SEP, height=1).pack(fill="x", padx=0)

    # ── UI build ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_nav()

        body = tk.Frame(self, bg=IOS_BG)
        body.pack(fill="both", pady=6)

        # ── URL card ───────────────────────────────────────────────────
        self._section_label(body, "YouTube URL")
        url_card = self._card(body)
        url_card.pack(fill="x", padx=12)

        url_row = tk.Frame(url_card, bg=IOS_CARD)
        url_row.pack(fill="x", padx=10, pady=9)

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(url_row,
                                  textvariable=self.url_var,
                                  font=IOS_FONT, bg=IOS_CARD, fg=IOS_TEXT,
                                  insertbackground=IOS_TEXT,
                                  relief="flat", bd=0, width=44)
        self.url_entry.pack(side="left", fill="x", expand=True)
        tk.Frame(url_row, bg=IOS_SEP, width=1).pack(side="left", fill="y", padx=8)
        iOSButton(url_row, "붙여넣기", self._paste_url,
                  color="blue", padx=12, pady=4,
                  font=IOS_FONT_SM, bg=IOS_CARD).pack(side="left")

        # ── Options card ───────────────────────────────────────────────
        self._section_label(body, "변환 옵션")
        opt_card = self._card(body)
        opt_card.pack(fill="x", padx=12)

        # FPS row
        fps_row = tk.Frame(opt_card, bg=IOS_CARD)
        fps_row.pack(fill="x", padx=14, pady=9)
        tk.Label(fps_row, text="FPS", font=IOS_FONT,
                 bg=IOS_CARD, fg=IOS_TEXT, width=10, anchor="w").pack(side="left")
        self.fps_var = tk.IntVar(value=15)
        tk.Spinbox(fps_row, from_=5, to=30, increment=5,
                   textvariable=self.fps_var,
                   width=5, font=IOS_FONT,
                   bg=IOS_CARD, fg=IOS_TEXT,
                   relief="solid", bd=1,
                   buttonbackground=IOS_BG).pack(side="left")

        self._row_sep(opt_card)

        # Scale row
        scale_row = tk.Frame(opt_card, bg=IOS_CARD)
        scale_row.pack(fill="x", padx=14, pady=9)
        tk.Label(scale_row, text="가로 크기", font=IOS_FONT,
                 bg=IOS_CARD, fg=IOS_TEXT, width=10, anchor="w").pack(side="left")
        self.scale_var = tk.IntVar(value=480)
        ttk.Combobox(scale_row, textvariable=self.scale_var,
                     values=[240, 320, 480, 640, 720],
                     width=8, state="readonly",
                     font=IOS_FONT).pack(side="left")

        self._row_sep(opt_card)

        # Directory row
        dir_row = tk.Frame(opt_card, bg=IOS_CARD)
        dir_row.pack(fill="x", padx=14, pady=9)
        tk.Label(dir_row, text="저장 위치", font=IOS_FONT,
                 bg=IOS_CARD, fg=IOS_TEXT, width=10, anchor="w").pack(side="left")
        self.outdir_var = tk.StringVar(value=OUTPUT_DIR)
        tk.Entry(dir_row, textvariable=self.outdir_var,
                 font=IOS_FONT_SM, bg=IOS_CARD, fg=IOS_TEXT_SEC,
                 relief="flat", bd=0, width=26,
                 state="readonly").pack(side="left", fill="x", expand=True)
        iOSButton(dir_row, "찾기", self._choose_dir,
                  color="gray", padx=12, pady=4,
                  font=IOS_FONT_SM, bg=IOS_CARD).pack(side="right")

        # ── Convert button ─────────────────────────────────────────────
        btn_outer = tk.Frame(body, bg=IOS_BG)
        btn_outer.pack(fill="x", padx=12, pady=(10, 4))
        self.convert_btn = iOSButton(btn_outer, "GIF 변환 시작", self._start_conversion,
                                      color="green", min_width=440,
                                      padx=20, pady=12,
                                      font=IOS_FONT_B, bg=IOS_BG)
        self.convert_btn.pack()

        # ── Status card ────────────────────────────────────────────────
        self._section_label(body, "상태")
        status_card = self._card(body)
        status_card.pack(fill="x", padx=12)
        status_inner = tk.Frame(status_card, bg=IOS_CARD)
        status_inner.pack(fill="x", padx=12, pady=9)

        self.progress_lbl = tk.Label(status_inner, text="대기 중...",
                                      font=IOS_FONT, bg=IOS_CARD, fg=IOS_TEXT_SEC,
                                      anchor="w")
        self.progress_lbl.pack(fill="x")
        self.progress = ttk.Progressbar(status_inner, mode="indeterminate",
                                         length=450, style="iOS.TProgressbar")
        self.progress.pack(fill="x", pady=(6, 0))

        # ── Result area ────────────────────────────────────────────────
        self.result_frame = tk.Frame(body, bg=IOS_BG)
        self.result_frame.pack(fill="x", padx=12, pady=(6, 8))

        result_card = self._card(self.result_frame)
        result_card.pack(side="left", fill="x", expand=True)
        self.result_lbl = tk.Label(result_card, text="",
                                    font=IOS_FONT_SM, bg=IOS_CARD, fg=IOS_TEXT,
                                    wraplength=360, justify="left", anchor="w",
                                    padx=10, pady=6)
        self.result_lbl.pack(fill="x")

        self.open_btn = iOSButton(self.result_frame, "Finder 열기", self._open_in_finder,
                                   color="blue", padx=12, pady=8,
                                   font=IOS_FONT_SM, bg=IOS_BG)
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
            args=(
                url,
                self.outdir_var.get(),
                self.fps_var,
                self.scale_var,
                self._on_progress,
                self._on_done,
                self._on_error,
            ),
            daemon=True,
        ).start()

    def _on_progress(self, msg):
        self.after(0, lambda: self.progress_lbl.config(text=msg, fg=IOS_TEXT_SEC))

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
        self.progress_lbl.config(
            text="완료!" if success else "오류 발생",
            fg="#1a72d4" if success else "#dd2020")
        self.result_lbl.config(
            text=msg,
            fg=IOS_TEXT if success else "#dd2020")
        if success and self._last_gif:
            self.open_btn.pack(side="right", padx=(8, 0))

    def _open_in_finder(self):
        if self._last_gif and os.path.exists(self._last_gif):
            subprocess.run(["open", "-R", self._last_gif])


if __name__ == "__main__":
    app = App()
    app.mainloop()
