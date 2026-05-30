# 小红砖 RedBrick 🧱

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20arm64-lightgrey)]()
[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()

小红书分享链接 → 提取正文 / OCR 图片 / 转录视频 → 结构化 JSON 输出，喂给任意 LLM 提炼知识点。

**零登录、纯本地、全部免费。**

---

## 它能干嘛

你把小红书看到的有价值内容（图文笔记、视频教程、行业分析）用分享链接发给它：

- 📝 **图文**：提取正文 + OCR 识别图片中的文字
- 🎬 **视频**：下载视频 → faster-whisper 转录成文字
- 📦 **输出**：一份结构化 JSON，扔给 ChatGPT / DeepSeek / Claude 就能提炼成知识点

> 最终形态：你每天刷小红书 → AI 自动帮你做笔记 → 只留下干货。

## 30 秒跑起来

### 前提：XHS-Downloader API 在跑

```bash
git clone https://github.com/JoeanAmier/XHS-Downloader.git && cd XHS-Downloader
pip install -r requirements.txt
python main.py api   # 默认 http://127.0.0.1:5556
```

### 安装 RedBrick

```bash
git clone https://github.com/CYOMI88/redbrick.git && cd redbrick
bash install.sh           # 装 Tesseract + Python 依赖
cp config.yaml.example config.yaml   # 改一下路径
```

### 跑一条

```bash
python pipeline.py "https://www.xiaohongshu.com/discovery/item/xxxxx?xsec_token=..."
```

输出：

```json
{
  "post_id": "6a1a806e0000000006033891",
  "title": "留给各种龙虾🦞&马🐴Agent的时间不多",
  "author": "时空旅人",
  "type": "图文",
  "full_text": "正文 + OCR 文字...",
  "files": {
    "raw.txt": "posts/6a1a8.../raw.txt",
    "ocr.txt": "posts/6a1a8.../ocr.txt"
  }
}
```

`full_text` 直接喂 LLM：

```bash
python pipeline.py "LINK" | jq -r '.full_text' | llm "提炼 3 条商业洞察"
```

## 架构

```
小红书链接
    │
    ▼
XHS-Downloader API（解析 + 下载）
    │
    ├── 图文 → Tesseract OCR → ocr.txt
    └── 视频 → faster-whisper → transcript.txt
    │
    ▼
结构化 JSON（full_text）
    │
    ▼
任意 LLM → 知识提炼
```

## 技术栈

| 组件 | 用途 | 许可 |
|------|------|------|
| [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) | 小红书内容解析 | GPL-3.0 |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 视频语音转录 | MIT |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | 图片文字识别 | Apache-2.0 |
| RedBrick 本身 | 胶水管线 | MIT |

全部免费，本地运行。

## 环境支持

- ✅ Linux x86_64 / ARM64（树莓派、Oracle Cloud A1.Flex 实测）
- ✅ macOS Apple Silicon（未测但理论可行）
- ❌ Windows（需要改 install.sh 或用 WSL）

## FAQ

**需要登录小红书吗？**
不用。分享链接本身就是公开内容，RedBrick 不碰任何账号信息。

**会被封号吗？**
RedBrick 只是胶水管线，不直接爬取数据。实际请求由 XHS-Downloader 发出。没有账号就无从封起。

**支持 xhslink.com 短链吗？**
`xhslink.com/m/*` 可尝试，`xhslink.com/o/*` 不支持。建议用小红书的"复制链接"功能获取完整链接（带 `xsec_token` 参数）。

**视频转录慢不慢？**
faster-whisper medium 模型，2 分钟视频约 4 分钟转录（Oracle A1.Flex ARM64 实测）。换 large-v3 更准但更慢。

**能提取评论区吗？**
需要登录，为安全考虑暂不支持。

## License

MIT
