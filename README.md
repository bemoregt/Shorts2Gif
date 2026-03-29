# short_gif

YouTube 영상(Shorts, 일반 링크)을 GIF로 변환하는 데스크탑 앱입니다.
Windows 2000 스타일의 레트로 UI로 제작되었습니다.

![Python](https://img.shields.io/badge/Python-3.x-blue) ![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)

---

## 스크린샷

![ScrShot 6](ScrShot%206.png)
![ScrShot 12](ScrShot%2012.png)
![ScrShot 13](ScrShot%2013.png)

---

## 기능

- YouTube Shorts, 일반 watch 링크, youtu.be 단축 URL 지원
- FPS, 가로 크기 조절 가능
- 고품질 GIF 변환 (ffmpeg 두 단계 팔레트 최적화)
- 실행 시 클립보드에서 YouTube URL 자동 감지
- 변환 완료 후 Finder에서 바로 열기
- Windows 2000 스타일 레트로 GUI

---

## 요구 사항

- Python 3.x
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/)

macOS에서 Homebrew로 설치:

```bash
brew install yt-dlp ffmpeg
```

---

## 실행

```bash
python3 app.py
```

---

## 사용법

1. YouTube URL 입력 또는 클립보드에서 자동 붙여넣기
2. FPS, 가로 크기, 저장 폴더 선택
3. **GIF 변환** 버튼 클릭
4. 완료 후 파일 경로 및 크기 확인, Finder에서 열기 가능

**변환 옵션**

| 옵션 | 기본값 | 선택 범위 |
|------|--------|-----------|
| FPS | 15 | 5 ~ 30 |
| 가로 크기 | 480px | 240 / 320 / 480 / 640 / 720 |
| 저장 경로 | ~/Downloads | 직접 선택 |

---

## 변환 방식

내부적으로 ffmpeg의 두 단계 변환을 사용합니다.

1. **팔레트 생성** — `palettegen=stats_mode=diff`로 최적 색상 팔레트 추출
2. **GIF 인코딩** — Lanczos 스케일링 + Bayer 디더링으로 고품질 출력

```
# 팔레트 생성
fps={fps},scale={width}:-1:flags=lanczos,palettegen=stats_mode=diff

# GIF 인코딩
fps={fps},scale={width}:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5
```
