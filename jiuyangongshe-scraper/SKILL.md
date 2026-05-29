---
name: jiuyangongshe-scraper
description: 抓取韭研公社(jiuyangongshe.com)产业库信息的工具。用于获取行业列表和行业详情内容，输出为 Markdown 格式。当用户需要抓取韭研公社产业库数据、获取行业研究报告或产业链信息时使用此 skill。
---

# 韭研公社产业库抓取工具

## 概述

此 skill 用于抓取韭研公社网站的产业库信息，支持：
- 抓取所有行业列表（约15个行业）
- 抓取指定行业的详细内容和个股明细
- 抓取所有行业的详情和个股明细
- 输出为 Markdown 格式便于阅读

**技术说明**：由于网站使用 JavaScript 动态加载数据，脚本使用 Playwright 模拟浏览器行为来获取完整数据。个股数据通常以图片形式呈现，脚本支持使用 OCR 技术识别图片中的股票代码和名称。

## 使用前提

### 1. 安装依赖

```bash
pip install playwright
playwright install chromium
```

如果需要识别图片中的个股数据，还需要安装OCR库：

```bash
pip install pytesseract pillow
```

**注意**：使用OCR功能需要安装 Tesseract 引擎：

#### macOS 安装方法：

**方法1：使用 Homebrew（推荐）**
```bash
brew install tesseract
```

如果遇到权限问题，尝试：
```bash
sudo chown -R $(whoami) /usr/local/Cellar /usr/local/Frameworks /usr/local/Homebrew /usr/local/bin /usr/local/etc /usr/local/include /usr/local/lib /usr/local/opt /usr/local/sbin /usr/local/share /usr/local/var/homebrew
brew install tesseract
```

**方法2：使用 MacPorts**
```bash
sudo port install tesseract
```

**方法3：手动安装**
从 https://github.com/UB-Mannheim/tesseract/wiki 下载 macOS 安装包

#### Ubuntu/Debian 安装方法：
```bash
sudo apt-get install tesseract-ocr
```

#### Windows 安装方法：
从 https://github.com/UB-Mannheim/tesseract/wiki 下载 Windows 安装包并安装

**重要说明**：
- OCR功能是**可选的**，即使不安装Tesseract，脚本仍然可以正常工作
- 如果没有安装Tesseract，脚本会跳过图片识别，但可以从其他来源提取个股数据
- 安装Tesseract后，脚本会自动识别图片中的股票代码和名称

### 2. 获取 Cookie

韭研公社网站需要登录才能访问产业库内容。用户需要提供有效的 Cookie。

**获取 Cookie 的方法**：
1. 在浏览器中登录 https://www.jiuyangongshe.com
2. 打开浏览器开发者工具（F12）
3. 切换到 Network/网络 标签
4. 刷新页面，找到任意请求
5. 在请求头中复制 Cookie 字段的值

## 使用方法

### 1. 抓取行业列表

```bash
python3 scripts/scraper.py --list --cookie "你的cookie字符串"
```

### 2. 抓取行业详情

```bash
python3 scripts/scraper.py --url "https://www.jiuyangongshe.com/industryChain/xxx" --cookie "你的cookie字符串"
```

### 3. 抓取所有行业及其个股明细

```bash
python3 scripts/scraper.py --all --cookie "你的cookie字符串" --output all_industries.md
```

### 4. 通过行业ID抓取详情

```bash
python3 scripts/scraper.py --industry-id "xxx" --cookie "你的cookie字符串"
```

### 5. 保存到文件

```bash
python3 scripts/scraper.py --list --cookie "你的cookie字符串" --output output.md
```

### 6. 同时输出 JSON

```bash
python3 scripts/scraper.py --list --cookie "你的cookie字符串" --output output.md --json
```

## 工作流程

当用户请求抓取韭研公社数据时：

1. **询问 Cookie**：如果用户没有提供 Cookie，询问用户获取 Cookie
2. **确认操作类型**：
   - 抓取所有行业列表 → 使用 `--list`
   - 抓取特定行业详情 → 使用 `--url`
   - 抓取所有行业及其个股明细 → 使用 `--all`
   - 通过行业ID抓取详情 → 使用 `--industry-id`
3. **执行抓取**：运行 scraper.py 脚本
4. **展示结果**：将 Markdown 结果展示给用户

## 脚本参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--cookie` | `-c` | 登录 Cookie（必需） |
| `--list` | `-l` | 抓取行业列表 |
| `--url` | `-u` | 指定详情页 URL |
| `--industry-id` | `-i` | 指定行业ID抓取详情 |
| `--all` | `-a` | 抓取所有行业及其个股明细 |
| `--output` | `-o` | 输出文件路径 |
| `--json` | `-j` | 同时输出 JSON 格式 |

## 注意事项

1. **Cookie 有效期**：Cookie 可能会过期，如果抓取失败请重新获取
2. **首次运行**：首次使用 Playwright 需要下载浏览器，可能需要一些时间
3. **请求频率**：避免过于频繁的请求，脚本已内置适当延迟

## 示例输出

抓取行业列表示例：

```markdown
# 韭研公社产业库 - 行业列表

来源: https://www.jiuyangongshe.com/industryChain

共找到 11 个行业

| 序号 | 行业名称 | 链接 |
|------|----------|------|
| 1 | 美、以-伊朗冲突(260301) | [链接](...) |
| 2 | 1. 有色金属(240407) | [链接](...) |
| 3 | 2. 光通信/光纤光缆(250608) | [链接](...) |
...
```
