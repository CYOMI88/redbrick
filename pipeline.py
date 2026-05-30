#!/usr/bin/env python3
"""
RedBrick — Xiaohongshu Content → Structured Text Pipeline
==========================================================
Takes a Xiaohongshu share link, extracts text content, runs OCR on images,
transcribes video audio, and outputs structured JSON ready for LLM processing.

Usage:
    python pipeline.py "https://www.xiaohongshu.com/discovery/item/xxxxx"

Config:
    Copy config.yaml.example to config.yaml and adjust paths.
    If tesseract or whisper sections are missing, those features are skipped.
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

import requests
import yaml

# ── Config ──────────────────────────────────────────────────────────


def load_config():
    config_paths = [
        Path(__file__).parent / "config.yaml",
        Path.home() / ".redbrick" / "config.yaml",
    ]
    for p in config_paths:
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f)
    # Sensible defaults
    return {
        "xhs_api": "http://127.0.0.1:5556/xhs/detail",
        "output_dir": "./posts",
        "download_dir": "./downloads",
    }


CONFIG = load_config()
XHS_API = CONFIG["xhs_api"]
OUTPUT_DIR = Path(CONFIG["output_dir"])
DOWNLOAD_DIR = Path(CONFIG["download_dir"])


# ── XHS-Downloader ───────────────────────────────────────────────────


def extract_post(url: str) -> dict:
    """Call XHS-Downloader API to get post details and download media."""
    resp = requests.post(
        XHS_API,
        json={"url": url, "download": True},
        timeout=60,
    )
    data = resp.json()
    if "data" not in data or not data["data"]:
        raise RuntimeError(f"XHS API error: {data.get('message', 'unknown')}")
    return data["data"]


# ── Tesseract OCR ────────────────────────────────────────────────────


def ocr_images(image_paths: list, config: dict) -> str:
    """Run Tesseract OCR on images. Returns empty string if not configured."""
    t = config.get("tesseract", {})
    if not t:
        return ""

    bin_path = os.path.expanduser(t.get("bin", "tesseract"))
    tessdata = os.path.expanduser(t.get("tessdata", ""))
    lang = t.get("lang", "chi_sim")

    texts = []
    for path in image_paths:
        output_base = str(Path(path).with_suffix(""))
        cmd = [bin_path, str(path), output_base, "-l", lang, "--psm", "6"]
        if tessdata:
            cmd.insert(2, "--tessdata-dir")
            cmd.insert(3, tessdata)
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
            txt_path = Path(output_base + ".txt")
            if txt_path.exists():
                text = txt_path.read_text().strip()
                if text:
                    texts.append(text)
        except Exception as e:
            print(f"OCR error on {path}: {e}", file=sys.stderr)
    return "\n\n".join(texts)


# ── faster-whisper ───────────────────────────────────────────────────


def transcribe_video(video_path: str, config: dict) -> str:
    """Transcribe video audio. Returns empty string if not configured."""
    w = config.get("whisper", {})
    if not w:
        return ""

    from faster_whisper import WhisperModel

    model = WhisperModel(
        w.get("model", "medium"),
        device=w.get("device", "cpu"),
        compute_type=w.get("compute_type", "int8"),
    )
    segments, _ = model.transcribe(video_path, language="zh")
    return " ".join(seg.text for seg in segments)


# ── File saving ─────────────────────────────────────────────────────


def save_post(post_id: str, files: dict):
    post_dir = OUTPUT_DIR / post_id
    post_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (post_dir / name).write_text(content, encoding="utf-8")


# ── Main ────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: pipeline.py <xiaohongshu_url>"}))
        sys.exit(1)

    url = sys.argv[1]
    post = extract_post(url)

    post_id = post.get("作品ID", datetime.now().strftime("%Y%m%d%H%M%S"))
    title = post.get("作品标题", "无标题")
    desc = post.get("作品描述", "")
    note_type = post.get("作品类型", "图文")
    author = post.get("作者昵称", "")

    files = {
        "raw.txt": f"标题: {title}\n作者: {author}\n\n正文:\n{desc}",
        "meta.yaml": yaml.dump(
            {
                "id": post_id,
                "title": title,
                "author": author,
                "type": note_type,
                "url": url,
                "extracted_at": datetime.now().isoformat(),
            },
            allow_unicode=True,
        ),
    }

    # OCR / Transcription
    ocr_text = ""
    transcript_text = ""

    if note_type == "视频":
        video_files = sorted(
            DOWNLOAD_DIR.glob("*.mp4"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if video_files:
            transcript_text = transcribe_video(str(video_files[0]), CONFIG)
            if transcript_text:
                files["transcript.txt"] = transcript_text
            video_files[0].unlink(missing_ok=True)
    else:
        image_files = sorted(
            [p for p in DOWNLOAD_DIR.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if image_files:
            ocr_text = ocr_images([str(p) for p in image_files[:10]], CONFIG)
            if ocr_text:
                files["ocr.txt"] = ocr_text
            for f in image_files[:10]:
                f.unlink(missing_ok=True)

    # Compile full text
    parts = [desc]
    if ocr_text:
        parts.append(f"\n--- 图片OCR ---\n{ocr_text}")
    if transcript_text:
        parts.append(f"\n--- 视频转录 ---\n{transcript_text}")
    full_text = "\n".join(p for p in parts if p)

    save_post(post_id, files)

    result = {
        "post_id": post_id,
        "title": title,
        "author": author,
        "type": note_type,
        "full_text": full_text,
        "ocr_chars": len(ocr_text),
        "transcript_chars": len(transcript_text),
        "files": {k: str(OUTPUT_DIR / post_id / k) for k in files},
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
