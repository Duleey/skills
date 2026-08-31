# Ark Voice Skill 使用示例

本文档收录典型场景的完整命令与预期输出。

---

## 🎤 TTS 场景

### 1. 最简调用

```bash
python3 scripts/tts.py --text "你好，欢迎使用语音合成服务。"
```

输出（stdout）：

```json
{
  "success": true,
  "error": null,
  "audio": {
    "local_path": "/Users/xxx/Desktop/Ark-Voice/tts/2026-08-31/tts_1788152923.mp3",
    "size_bytes": 25965,
    "format": "mp3",
    "sample_rate": 24000
  },
  "metadata": {
    "text": "你好，欢迎使用语音合成服务。",
    "speaker": "zh_female_vv_uranus_bigtts",
    "generation_time": 0.95,
    "model": "doubao-seed-tts-2.0",
    "save_dir": "/Users/xxx/Desktop/Ark-Voice/tts/2026-08-31"
  }
}
```

### 2. 换音色 + 调语速

```bash
python3 scripts/tts.py \
  --text "各位好，今天的会议现在开始。" \
  --speaker 高冷御姐 \
  --speed 0.9
```

### 3. 指定输出位置

```bash
python3 scripts/tts.py --text "保存到指定位置" --output ~/Downloads/demo.mp3
```

### 4. 生成高保真 wav

```bash
python3 scripts/tts.py \
  --text "高保真音频输出" \
  --format wav \
  --sample-rate 48000
```

### 5. 长文本朗读

单次最长 3000 字符。更长的内容应由 Agent 层按句切分后多次调用，再按需合并音频。

```bash
python3 scripts/tts.py --text "$(cat article.txt)" --output ~/Desktop/article.mp3
```

---

## 🎧 ASR 场景

### 1. 最简调用

```bash
python3 scripts/asr.py --audio speech.wav
```

输出（stdout）：

```json
{
  "success": true,
  "error": null,
  "text": "今天天气很好，我准备去公园散步。",
  "utterances": [],
  "metadata": {
    "audio_path": "/tmp/speech.wav",
    "audio_duration": 2.98,
    "recognition_time": 3.44,
    "mode": "stream",
    "model": "doubao-seed-asr-2.0"
  }
}
```

stderr 会实时显示增量出字过程：

```
   今天
   今天天气
   今天天气很好
   今天天气很好，我准备去公园散步。
```

### 2. 先转码再识别（最常见）

用户给的音频通常不是 16k 单声道 wav，必须先转：

```bash
ffmpeg -i input.m4a -ar 16000 -ac 1 -acodec pcm_s16le /tmp/converted.wav
python3 scripts/asr.py --audio /tmp/converted.wav
```

### 3. 会议记录：准确率优先 + 分句时间戳

```bash
python3 scripts/asr.py \
  --audio meeting.wav \
  --mode accurate \
  --utterances
```

`utterances` 字段会返回每句的起止时间与逐字时间戳，可用于生成字幕：

```json
[
  {
    "text": "方舟大模型支持语音合成和语音识别两大能力。",
    "start_time": 0,
    "end_time": 4080,
    "words": [
      { "text": "方", "start_time": 240, "end_time": 400 },
      { "text": "舟", "start_time": 400, "end_time": 560 }
    ]
  }
]
```

### 4. 专有名词识别：热词

```bash
python3 scripts/asr.py \
  --audio product_review.wav \
  --hotwords "火山方舟,豆包,Seedream,Agent Plan"
```

### 5. 口语转书面语：语义顺滑

去掉「嗯」「那个」等口头语和重复词：

```bash
python3 scripts/asr.py --audio interview.wav --ddc
```

### 6. 保留原始口语文本

```bash
python3 scripts/asr.py --audio raw.wav --no-punc --no-itn
```

---

## 🔄 组合场景

### TTS → ASR 闭环自检

验证 API Key 与链路是否正常，也可用于回归测试：

```bash
python3 scripts/tts.py \
  --text "今天天气很好，我准备去公园散步。" \
  --format wav --sample-rate 16000 \
  --output /tmp/roundtrip.wav

python3 scripts/asr.py --audio /tmp/roundtrip.wav
```

识别结果应与输入文本一致。

### 音频翻译工作流

```bash
# 1. 识别原音频
python3 scripts/asr.py --audio source.wav > transcript.json

# 2. Agent 层调用语言模型翻译 transcript.json 中的 text 字段

# 3. 合成译文语音
python3 scripts/tts.py --text "<翻译后的文本>" --output translated.mp3
```

---

## ❌ 错误示例

### 音频格式不符

```bash
python3 scripts/asr.py --audio music.mp3
```

```json
{
  "success": false,
  "error": "Not a valid WAV file: file does not start with RIFF id\nConvert first: ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav",
  "text": null,
  "metadata": null
}
```

处理方式：Agent 应按提示自动执行 ffmpeg 转码后重试。

### 采样率不符

```json
{
  "success": false,
  "error": "Audio must be 16000 Hz / 1 channel / 16-bit, got 44100 Hz / 2 channel / 16-bit.\nConvert first: ffmpeg -i input.wav -ar 16000 -ac 1 -acodec pcm_s16le output.wav"
}
```

### 参数不合法

```bash
python3 scripts/tts.py --text "x" --format flac
```

```
Parameter validation failed:
  - --format must be one of mp3/wav/pcm/ogg_opus
```

脚本在发起 API 调用前就会拦截，不会浪费额度。
