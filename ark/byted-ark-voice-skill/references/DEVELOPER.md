# Ark Voice Skill 开发指南

面向 Agent 开发者与维护者，记录协议实现细节、踩坑点与对接规范。

---

## 📁 文件结构

```
byted-ark-voice-skill/
├── SKILL.md                  # Skill 说明与触发条件
├── scripts/
│   ├── common.py             # API Key 检测、端点常量、输出路径
│   ├── ws_client.py          # 标准库手写的极简 WebSocket 客户端
│   ├── tts.py                # 语音合成（HTTP chunked streaming）
│   └── asr.py                # 语音识别（WebSocket 二进制协议）
└── references/
    ├── EXAMPLES.md
    └── DEVELOPER.md
```

**零第三方依赖**：仅使用 Python 标准库（`urllib`、`socket`、`ssl`、`gzip`、`struct`、`wave`、`threading`）。因此不需要 `pip install websockets` 或 `requests`，拷贝即用。

---

## 🔌 接口选型

方舟 Agent Plan 语音接口的路径带 `/plan/` 前缀，与普通版接口不同。

### TTS

| 接口 | 协议 | 地址 | 本 Skill |
|------|------|------|---------|
| 双向流式 | WebSocket | `/api/v3/plan/tts/bidirection` | 未用 |
| 单向流式 | WebSocket | `/api/v3/plan/tts/unidirectional/stream` | 未用 |
| **HTTP** | **HTTP POST** | **`/api/v3/plan/tts/unidirectional`** | **✅ 采用** |

选 HTTP 接口的原因：一次性发文本、流式收音频，已能满足文件落盘场景，且用 `urllib` 即可实现，无需 WebSocket。

鉴权头：

```
X-Api-Key: ark-xxx
X-Api-Resource-Id: seed-tts-2.0
Content-Type: application/json
```

响应是**按行分隔的 JSON**，每行可能含 base64 编码的 `data` 字段：

```python
for raw_line in response:
    chunk = json.loads(raw_line)
    if chunk.get("code") == 20000000:   # 20000000 = 合成结束
        break
    if chunk.get("code"):               # 其他非零 = 错误
        raise SystemExit(chunk["message"])
    if chunk.get("data"):
        audio.extend(base64.b64decode(chunk["data"]))
```

### ASR

| 接口 | 协议 | 地址 | 对应 `--mode` |
|------|------|------|--------------|
| 双向流式（优化版） | WebSocket | `/api/v3/plan/sauc/bigmodel_async` | `stream` |
| 流式输入 | WebSocket | `/api/v3/plan/sauc/bigmodel_nostream` | `accurate` |

鉴权头：

```
X-Api-Key: ark-xxx
X-Api-Resource-Id: volc.seedasr.sauc.duration
X-Api-Request-Id: <uuid>
X-Api-Connect-Id: <uuid>
```

握手响应头中的 `X-Tt-Logid` 是排障关键，脚本会打印到 stderr。

---

## 📦 ASR 二进制协议

所有整数字段用**大端**表示。帧结构：

```
+--------+--------+--------+--------+
| 4-byte header                     |
+-----------------------------------+
| sequence (4B, int32, 可选)        |
+-----------------------------------+
| payload size (4B, uint32)         |
+-----------------------------------+
| payload (gzip 压缩)               |
+-----------------------------------+
```

### header 4 字节布局

| 字节 | 高 4 位 | 低 4 位 |
|------|--------|--------|
| 0 | protocol version = `0b0001` | header size = `0b0001`（实际长度 = 值 × 4） |
| 1 | message type | message type specific flags |
| 2 | serialization method | compression |
| 3 | reserved = `0x00` | |

message type：

- `0b0001` full client request（首包，携带 JSON 参数）
- `0b0010` audio only request（音频包）
- `0b1001` full server response
- `0b1111` server error

flags：

- `0b0000` 无 sequence 字段
- `0b0001` 有 sequence，且为正
- `0b0010` 无 sequence，仅标识最后一包
- `0b0011` 有 sequence，且为负（最后一包）

### 交互流程

1. 建连（HTTP GET + Upgrade，带鉴权头）
2. 发 full client request：JSON 参数 gzip 压缩，seq = 1
3. 收 ACK（服务端返回 full server response）
4. 循环发 audio only request：seq 递增，最后一包 flags 用 `0b0011` 且 seq 取负
5. 收识别结果，直到 `is_last`

---

## 🐛 实现踩坑记录

以下三个问题均为实测中发现并修复，改动时请勿回退。

### 1. 音频 format 必须声明为 `pcm`，不能是 `wav`

用 Python `wave` 模块读出的是**已剥离容器头的裸 PCM 数据**。若首包 JSON 里声明 `"format": "wav"`，服务端会按 wav 解析而收到裸 PCM，报错：

```
[Invalid audio format] OperatorWrapper Process failed
```

正确做法：声明 `"format": "pcm"`, `"codec": "raw"`。

### 2. 响应帧的 sequence 字段是**可选**的

服务端 ACK 帧 header 为 `11 90 10 00`，flags = `0b0000`，即**不带 sequence**，且 payload 未压缩（compression 位为 `0`）。

因此解析时必须：
- 仅当 flags 为 `0b0001` / `0b0011` 时才读 4 字节 sequence
- 严格按 header 的 compression / serialization 位决定是否 gzip 解压、是否 JSON 解析

不能假定「响应一定带 sequence」或「响应一定 gzip 压缩」，否则偏移量错位导致 `JSONDecodeError`。

### 3. `bigmodel_async` 不是每包必回，同步收发会死锁

优化版双向流式**只在识别结果变化时才推送**响应。若代码写成「发一包 → 阻塞 recv 一包」，当服务端选择不回包时会永久阻塞。

解决方案：发送放在独立线程，主线程专职循环 `recv()`。

```python
sender = threading.Thread(target=send_all, daemon=True)
sender.start()
while True:
    frame = ws.recv()
    ...
    if response["is_last"]:
        break
```

同时 `WebSocket.send()` 内部加锁，避免发送线程与接收线程交错写 socket 造成帧损坏。

---

## 🌐 WebSocket 客户端实现要点

`ws_client.py` 实现了 RFC 6455 的必要子集：

- **握手**：手写 HTTP GET + `Upgrade: websocket`，`Sec-WebSocket-Key` 用 `os.urandom(16)` 的 base64；校验响应首行含 `101`
- **掩码**：客户端发出的帧**必须**掩码（`0x80 | len`，附 4 字节随机 mask）
- **变长长度**：< 126 直接写；< 65536 用 2 字节；否则 8 字节
- **分片重组**：`recv()` 会拼接 continuation 帧直到 FIN
- **控制帧**：自动回 PONG，收到 CLOSE 返回 `None`
- **线程安全**：`send()` 由 `threading.Lock` 保护

未实现（当前场景不需要）：`Sec-WebSocket-Accept` 校验、扩展协商、客户端分片发送。

---

## 🎯 Agent 层对接规范

### stderr / stdout 分离

| 输出流 | 内容 | Agent 处理方式 |
|--------|------|---------------|
| **stderr** | 进度、日志、增量出字 | 逐行展示给用户看 |
| **stdout** | 单个 JSON 结果对象 | 解析后结构化展示，**不要直接打印** |

```python
proc = subprocess.run([...], capture_output=True, text=True)
show_progress(proc.stderr)          # 实时反馈
result = json.loads(proc.stdout)    # 结构化结果

if result["success"]:
    send_file_to_user(result["audio"]["local_path"])   # TTS：把文件发给用户
else:
    handle_error(result["error"])
```

### 统一错误契约

无论何种失败，stdout 都输出：

```json
{ "success": false, "error": "<message>", "text": null, "metadata": null }
```

退出码为 `1`。Agent 可只判断 `success` 字段。

### ASR 前置转码责任

Agent 层**必须**负责把用户音频转成 16k/16bit/单声道 wav，不要把格式错误抛给用户：

```bash
ffmpeg -i input.<ext> -ar 16000 -ac 1 -acodec pcm_s16le output.wav
```

脚本已在错误信息里内置这条命令，可直接提取执行。

---

## ✅ 回归验证方法

改动后用 TTS → ASR 闭环自检，识别结果应与输入文本一致：

```bash
python3 scripts/tts.py --text "今天天气很好，我准备去公园散步。" \
  --format wav --sample-rate 16000 --output /tmp/rt.wav
python3 scripts/asr.py --audio /tmp/rt.wav
```

同时应覆盖：

- `--mode accurate` 与 `--utterances`（分句时间戳非空）
- 中文音色预设名映射（如 `--speaker 高冷御姐`）
- 参数校验拦截（如 `--format flac` 应在调用前报错）
- 文件不存在、格式不符的结构化错误输出

---

## 🔧 环境变量

| 变量 | 说明 |
|------|------|
| `ARK_API_KEY` | API Key（也支持 `API_KEY` 等通用命名兜底） |
| `ARK_VOICE_SAVE_PATH` | 覆盖默认输出目录 |

输出目录三级降级：环境变量/`--output-dir` > `~/Desktop/Ark-Voice/...` > `~/Ark-Voice/...` > `./Ark-Voice/...`，并自动按日期建子目录。
