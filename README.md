# RedNote Slide Clipper (`rednote-slide-clipper`)

**Turn multi-slide visual carousels (mindmaps, tables, comparison charts, checklists) from RedNote (Xiaohongshu) & visual web pages into clean, searchable Obsidian Markdown in seconds — powered by 100% local, zero-token `RapidOCR`.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Offline OCR](https://img.shields.io/badge/OCR-RapidOCR%20ONNX-0E7C4A.svg)](#why-this-exists)

[English](#why-this-exists) | [简体中文](#简体中文说明)

---

## Why This Exists

On visual knowledge platforms like **RedNote (Xiaohongshu)**, 90% of the real value — industry mindmaps, specification tables, SOP checklists, and frameworks — is locked inside **8 to 18 swipeable carousel images**, while the text caption is only a two-line hook.

Traditional web clippers (Obsidian Web Clipper, Readwise, Cubox) only grab the caption text, leaving your knowledge vault blind to the actual content inside the slides.

**`rednote-slide-clipper`** solves this cleanly on your local machine:
- **100% Local & Zero API Tokens**: Uses `rapidocr-onnxruntime` locally on CPU — no cloud vision API bills, no privacy leaks.
- **Zero Image Clutter**: Extracts slide text page-by-page into structured Markdown bullets and immediately removes temporary slide images.
- **Obsidian-First YAML Frontmatter**: Ready to drop straight into your Obsidian vault for instant full-text search and AI RAG indexing.

---

## Quick Start

```bash
git clone https://github.com/bsjzmj/rednote-slide-clipper.git
cd rednote-slide-clipper
pip install -r requirements.txt
playwright install chromium
```

### Clip a Single Visual Post into Obsidian Markdown (MIT Free Core)

```bash
python clipper.py --url "https://www.xiaohongshu.com/explore/<post_id>?xsec_token=..." --out "./notes"
```

### Run Offline Self-Test

```bash
python clipper.py --self-test
```

---

## Open-Core Tiers (MIT Free Core vs Optional Pro Synthesis Lenses)

The core slide-to-Markdown OCR clipper is **100% free and MIT-licensed** with zero rate limits or nag screens. An optional offline `Ed25519` Pro key unlocks structured synthesis templates:

| Feature | MIT Free Core | Pro Lens Edition |
| :--- | :---: | :---: |
| Single-post caption + YAML metadata clipping | Yes | Yes |
| Local zero-token `RapidOCR` across up to 18 carousel slides | Yes | Yes |
| Automatic temporary image cleanup (zero disk bloat) | Yes | Yes |
| Auto-generated **Mermaid Mindmap** from slide hierarchy | - | Yes |
| **Consensus vs. Counter-Consensus Pitfall Radar** from visible comments | - | Yes |
| **4 Domain Analytical Checklists** (`cross-border`, `hardtech`, `high-ticket`, `general`) | - | Yes |

```bash
# Optional: Activate an offline Ed25519 Pro key (0ms network overhead)
python clipper.py --activate "RMC1.<payload>.<signature>"
python clipper.py --url "<post_url>" --lens cross-border --out "./notes"
```

---

## Fair-Use & Compliance Notice

This tool is strictly a **user-initiated personal learning & note-taking clipper** (similar to Obsidian Web Clipper or Readwise Reader) intended for organizing single public pages that you are reading for personal study and research.
- Contains **zero** cryptographic signature reverse-engineering or anti-bot bypass code.
- Contains **zero** bulk account scraping, automated messaging, or watermark-stripping repost pipelines.
- Please respect content creators' copyrights and platform Terms of Service.

---

## 简体中文说明

### 痛点与定位

在小红书等视觉化知识平台上，真正硬核的干货（行业思维导图、参数对比表、SOP 清单、避坑指南）几乎全藏在 **10～18 张滑动图片** 里，正文往往只有两句标题党。普通网页剪藏工具只能抓正文，存进 Obsidian 里根本搜不到图片里的核心文字。

**`rednote-slide-clipper`** 是一个极简、干净的**本地单篇图文学习剪藏助手**：
1. **纯本地离线零 Token 识别**：基于 `rapidocr-onnxruntime` 离线提取最多 18 页幻灯片文字，无需消耗大模型视觉 Token；
2. **零磁盘图片垃圾残留**：识别完文字生成结构化 Markdown 后自动清理临时缓存图；
3. **安全合规（Open-Core 架构）**：MIT 免费版完整开放单篇正文与全量幻灯片 OCR 提取；可选的 Pro 透镜层（采用纯离线 `Ed25519` 公钥验签，`<0.2ms` 零性能损耗）额外解锁 **自动 Mermaid 思维导图、评论区“主流共识 vs 冷门避坑反共识”聚类、以及四大商业拆解透镜（跨境选品 / 硬科技投研 / 高客单说服 / 通用商业）**。

### 快速使用

```bash
pip install -r requirements.txt
playwright install chromium

# 剪藏单篇图文笔记并自动跑离线 OCR 生成 Obsidian 笔记
python clipper.py --url "单篇公开笔记链接" --out "./notes"
```

> **合理使用声明**：本工具仅作为个人学习研究与单篇公开阅读笔记整理辅助工具（不含任何平台协议逆向、不含批量爬主页或自动群控代码），请严格遵守著作权法与平台服务条款，尊重原作者原创权益。
