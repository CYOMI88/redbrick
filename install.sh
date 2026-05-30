#!/bin/bash
# RedBrick — 一键安装依赖
set -e

ARCH=$(uname -m)
echo " Architecture: $ARCH"

# 1. Python deps
echo "Installing Python dependencies..."
pip install requests pyyaml pillow faster-whisper 2>/dev/null || pip3 install requests pyyaml pillow faster-whisper

# 2. Tesseract (static binary)
if [ ! -f "$HOME/tesseract/tesseract" ]; then
    echo "Downloading Tesseract..."
    mkdir -p "$HOME/tesseract/tessdata"

    case $ARCH in
        aarch64|arm64)
            TESS_URL="https://github.com/DanielMYT/tesseract-static/releases/download/tesseract-5.5.2/tesseract.aarch64"
            ;;
        x86_64|amd64)
            TESS_URL="https://github.com/DanielMYT/tesseract-static/releases/download/tesseract-5.5.2/tesseract.x86_64"
            ;;
        *)
            echo "Unsupported architecture: $ARCH. Skip Tesseract or install manually."
            exit 0
            ;;
    esac

    curl -L -o "$HOME/tesseract/tesseract" "$TESS_URL"
    chmod +x "$HOME/tesseract/tesseract"

    # Chinese language pack
    curl -L -o "$HOME/tesseract/tessdata/chi_sim.traineddata" \
        "https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata"

    echo "Tesseract installed: $HOME/tesseract/"
else
    echo "Tesseract already installed."
fi

# 3. Config
if [ ! -f config.yaml ]; then
    cp config.yaml.example config.yaml
    echo "Created config.yaml — edit paths if needed."
fi

echo ""
echo "Done. Next:"
echo "  1. Start XHS-Downloader: cd XHS-Downloader && python main.py api"
echo "  2. Run: python pipeline.py 'XHS_LINK'"
