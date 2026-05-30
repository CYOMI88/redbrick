# RedBrick — 小红书知识提取管线

RedBrick 将小红书分享链接一键转化为结构化文本：提取正文、OCR 图片文字、转录视频语音，输出 JSON 供任意 LLM 提炼知识点。

## 三句话

- 发一个小红书链接 → 得到一份结构化 JSON
- 图文帖自动 OCR 图片中的文字，视频帖自动语音转文字
- 不依赖任何付费 API，所有工具本地免费跑

## 支持的内容类型

| 类型 | 处理方式 | 输出 |
|------|---------|------|
| 图文（有正文） | 直接提取 | `raw.txt` |
| 图文（纯图片） | Tesseract OCR | `ocr.txt` |
| 视频 | faster-whisper 转录 | `transcript.txt` |

## 安装

### 1. XHS-Downloader（小红书解析）

```bash
git clone https://github.com/JoeanAmier/XHS-Downloader.git
cd XHS-Downloader
pip install -r requirements.txt
```

启动 API：
```bash
python main.py api  # 默认端口 5556
```

### 2. faster-whisper（视频转录）

```bash
pip install faster-whisper
```

### 3. Tesseract（图片 OCR）

```bash
# 下载 ARM64 静态编译版本
mkdir -p ~/tesseract/tessdata
curl -L -o ~/tesseract/tesseract https://github.com/DanielMYT/tesseract-static/releases/download/tesseract-5.5.2/tesseract.aarch64
chmod +x ~/tesseract/tesseract

# 中文语言包
curl -L -o ~/tesseract/tessdata/chi_sim.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata
```

x86_64 用户替换 `tesseract.aarch64` 为 `tesseract.x86_64`。

### 4. RedBrick

```bash
git clone https://github.com/YOUR_USERNAME/redbrick.git
cd redbrick
pip install requests pyyaml pillow
```

编辑 `config.yaml`，设置各工具的路径。

## 使用

```bash
python pipeline.py "https://www.xiaohongshu.com/discovery/item/xxxxx?xsec_token=..."
```

输出 JSON：
```json
{
  "post_id": "6a1a806e0000000006033891",
  "title": "留给各种龙虾 & 马 Agent 的时间不多",
  "type": "图文",
  "full_text": "正文文字 + OCR 文字...",
  "files": {
    "raw.txt": "...",
    "ocr.txt": "..."
  }
}
```

`full_text` 可喂给任意 LLM 做知识提炼：

```bash
python pipeline.py "LINK" | jq -r '.full_text' | your-llm-cli "提炼3条商业洞察"
```

## 架构

```
小红书链接
    │
    ▼
XHS-Downloader API（解析 + 下载）
    │
    ├── 图文：Tesseract OCR 图片
    └── 视频：faster-whisper 转录
    │
    ▼
结构化 JSON（full_text）
    │
    ▼
任意 LLM / 知识库
```

## 依赖与成本

| 组件 | 许可 | 成本 |
|------|------|------|
| XHS-Downloader | GPL-3.0 | 免费 |
| faster-whisper | MIT | 免费 |
| Tesseract | Apache-2.0 | 免费 |
| RedBrick 本身 | MIT | 免费 |

## 常见问题

**需要登录小红书吗？** 不用。但未登录时视频画质较低。

**会被封号吗？** RedBrick 只是胶水代码，不直接爬取数据。实际请求由 XHS-Downloader 发出。

**支持 xhslink.com 短链吗？** 目前仅支持完整链接（`xiaohongshu.com/discovery/item/...` 或 `xiaohongshu.com/explore/...`）。短链格式变动频繁。

**OCR 不准怎么办？** Tesseract 对清晰截图效果好，对手写体/花体效果差。可自行替换为其他 OCR 引擎。

## 许可

MIT
