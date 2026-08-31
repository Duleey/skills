#!/usr/bin/env python3
"""
Ark Agent Plan ASR (Automatic Speech Recognition) — doubao-seed-asr-2.0

Streams a local WAV file to the Agent Plan streaming recognition endpoint over
WebSocket and prints the transcript. Progress goes to stderr; a single JSON
result object goes to stdout.

Audio requirement: 16 kHz / 16-bit / mono PCM WAV. Convert other formats first,
e.g. `ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav`.

Usage:
    python3 scripts/asr.py --audio /path/to/speech.wav

@license MIT
"""

from __future__ import annotations

import argparse
import gzip
import json
import struct
import sys
import threading
import time
import uuid
import wave
from pathlib import Path
from typing import Optional

from common import (
    ASR_BITS,
    ASR_CHANNELS,
    ASR_RESOURCE_ID,
    ASR_SAMPLE_RATE,
    ASR_WS_ASYNC_URL,
    ASR_WS_NOSTREAM_URL,
    resolve_api_key,
)
from ws_client import WebSocket, WebSocketError

# --- Ark binary protocol constants (big-endian integers throughout) ---
PROTOCOL_VERSION = 0b0001
HEADER_SIZE = 0b0001  # header length = value * 4 bytes

MSG_FULL_CLIENT_REQUEST = 0b0001
MSG_AUDIO_ONLY_REQUEST = 0b0010
MSG_FULL_SERVER_RESPONSE = 0b1001
MSG_SERVER_ERROR = 0b1111

FLAG_NO_SEQUENCE = 0b0000
FLAG_POS_SEQUENCE = 0b0001
FLAG_LAST_NO_SEQUENCE = 0b0010
FLAG_NEG_WITH_SEQUENCE = 0b0011

SERIALIZATION_JSON = 0b0001
SERIALIZATION_NONE = 0b0000
COMPRESSION_GZIP = 0b0001

# 200 ms per packet is the documented sweet spot for the streaming endpoint.
CHUNK_MS = 200
BYTES_PER_SAMPLE = ASR_BITS // 8
CHUNK_BYTES = ASR_SAMPLE_RATE * BYTES_PER_SAMPLE * ASR_CHANNELS * CHUNK_MS // 1000


def log(message: str = "") -> None:
    """Write progress information to stderr so stdout stays machine-readable."""
    print(message, file=sys.stderr, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ark Agent Plan speech recognition")
    parser.add_argument("--audio", required=True, help="path to a 16 kHz mono WAV file")
    parser.add_argument(
        "--mode",
        default="stream",
        choices=("stream", "accurate"),
        help="stream: low latency incremental results; accurate: higher accuracy",
    )
    parser.add_argument(
        "--no-punc", action="store_true", help="disable automatic punctuation"
    )
    parser.add_argument(
        "--no-itn",
        action="store_true",
        help="disable inverse text normalisation (e.g. 一九七零年 -> 1970年)",
    )
    parser.add_argument(
        "--ddc", action="store_true", help="enable disfluency removal (语义顺滑)"
    )
    parser.add_argument(
        "--utterances", action="store_true", help="return per-sentence details"
    )
    parser.add_argument(
        "--hotwords",
        default=None,
        help="comma-separated hot words to boost recognition accuracy",
    )
    parser.add_argument("--api-key", dest="api_key", default=None)
    parser.add_argument("--timeout", type=int, default=120)
    return parser.parse_args()


def build_header(
    message_type: int, flags: int, serialization: int = SERIALIZATION_JSON
) -> bytes:
    """Pack the 4-byte protocol header."""
    return bytes(
        [
            (PROTOCOL_VERSION << 4) | HEADER_SIZE,
            (message_type << 4) | flags,
            (serialization << 4) | COMPRESSION_GZIP,
            0x00,
        ]
    )


def read_wav(path: Path) -> bytes:
    """Read raw PCM frames, enforcing the format the service requires."""
    if not path.exists():
        raise SystemExit(f"Audio file not found: {path}")
    try:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            rate = wav.getframerate()
            frames = wav.readframes(wav.getnframes())
    except wave.Error as exc:
        raise SystemExit(
            f"Not a valid WAV file: {exc}\n"
            "Convert first: ffmpeg -i input.mp3 -ar 16000 -ac 1 "
            "-acodec pcm_s16le output.wav"
        ) from exc

    if (rate, channels, width) != (ASR_SAMPLE_RATE, ASR_CHANNELS, BYTES_PER_SAMPLE):
        raise SystemExit(
            f"Audio must be {ASR_SAMPLE_RATE} Hz / {ASR_CHANNELS} channel / "
            f"{ASR_BITS}-bit, got {rate} Hz / {channels} channel / {width * 8}-bit.\n"
            "Convert first: ffmpeg -i input.wav -ar 16000 -ac 1 "
            "-acodec pcm_s16le output.wav"
        )
    if not frames:
        raise SystemExit("Audio file contains no samples")
    return frames


def build_request_payload(args: argparse.Namespace) -> dict:
    request: dict[str, object] = {
        "model_name": "bigmodel",
        "enable_itn": not args.no_itn,
        "enable_punc": not args.no_punc,
        "enable_ddc": args.ddc,
        "show_utterances": args.utterances,
    }
    if args.hotwords:
        words = [w.strip() for w in args.hotwords.split(",") if w.strip()]
        if words:
            # Hot words are passed as a nested JSON string per the API contract.
            request["corpus"] = {
                "context": json.dumps(
                    {"hotwords": [{"word": w} for w in words]}, ensure_ascii=False
                )
            }
    return {
        "user": {"uid": "ark-voice-skill"},
        "audio": {
            # We strip the WAV container and stream raw PCM frames.
            "format": "pcm",
            "codec": "raw",
            "rate": ASR_SAMPLE_RATE,
            "bits": ASR_BITS,
            "channel": ASR_CHANNELS,
        },
        "request": request,
    }


def pack_full_request(payload: dict, seq: int) -> bytes:
    compressed = gzip.compress(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return (
        build_header(MSG_FULL_CLIENT_REQUEST, FLAG_POS_SEQUENCE)
        + struct.pack(">i", seq)
        + struct.pack(">I", len(compressed))
        + compressed
    )


def pack_audio_request(chunk: bytes, seq: int, is_last: bool) -> bytes:
    """Pack an audio frame; the final packet carries a negative sequence number."""
    flags = FLAG_NEG_WITH_SEQUENCE if is_last else FLAG_POS_SEQUENCE
    sequence = -seq if is_last else seq
    compressed = gzip.compress(chunk)
    return (
        build_header(MSG_AUDIO_ONLY_REQUEST, flags, SERIALIZATION_NONE)
        + struct.pack(">i", sequence)
        + struct.pack(">I", len(compressed))
        + compressed
    )


def parse_response(frame: bytes) -> dict:
    """Decode one server frame into a dict describing its type and payload.

    The server omits the sequence field unless the flags say otherwise, and it
    echoes the compression/serialization bits in the header, so both must be
    read from the frame rather than assumed.
    """
    if len(frame) < 4:
        raise WebSocketError(f"Response frame too short: {len(frame)} bytes")

    message_type = frame[1] >> 4
    flags = frame[1] & 0x0F
    serialization = frame[2] >> 4
    compression = frame[2] & 0x0F

    offset = (frame[0] & 0x0F) * 4
    sequence = None
    # Only flags 0b0001 / 0b0011 carry a 4-byte sequence number.
    if flags in (FLAG_POS_SEQUENCE, FLAG_NEG_WITH_SEQUENCE):
        (sequence,) = struct.unpack(">i", frame[offset : offset + 4])
        offset += 4

    body = b""
    if len(frame) >= offset + 4:
        (size,) = struct.unpack(">I", frame[offset : offset + 4])
        offset += 4
        body = frame[offset : offset + size]

    if body and compression == COMPRESSION_GZIP:
        body = gzip.decompress(body)

    payload: object = body
    if body and serialization == SERIALIZATION_JSON:
        payload = json.loads(body.decode("utf-8"))

    return {
        "type": message_type,
        "sequence": sequence,
        "is_last": flags in (FLAG_LAST_NO_SEQUENCE, FLAG_NEG_WITH_SEQUENCE),
        "payload": payload,
    }


def extract_text(payload: object) -> Optional[str]:
    """Pull the transcript out of a server response payload."""
    if not isinstance(payload, dict):
        return None
    result = payload.get("result")
    if isinstance(result, dict):
        return result.get("text")
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict):
            return first.get("text")
    return None


def recognize(api_key: str, audio: bytes, args: argparse.Namespace) -> dict:
    """Stream the audio and return the final transcript plus raw utterances.

    The service does not answer every audio packet: it pushes a response only
    when the transcript changes. Sending therefore runs on a worker thread while
    the main thread consumes responses, otherwise a blocking recv() after each
    packet would deadlock.
    """
    url = ASR_WS_ASYNC_URL if args.mode == "stream" else ASR_WS_NOSTREAM_URL
    request_id = str(uuid.uuid4())
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": ASR_RESOURCE_ID,
        "X-Api-Request-Id": request_id,
        "X-Api-Connect-Id": request_id,
    }

    transcript = ""
    utterances: list = []

    with WebSocket(url, headers, timeout=args.timeout) as ws:
        log(f"connected (logid: {ws.response_headers.get('x-tt-logid', 'n/a')})")

        ws.send(pack_full_request(build_request_payload(args), 1))
        ack = parse_response(ws.recv() or b"")
        if ack["type"] == MSG_SERVER_ERROR:
            raise SystemExit(f"ASR rejected the request: {ack['payload']}")

        chunks = [audio[i : i + CHUNK_BYTES] for i in range(0, len(audio), CHUNK_BYTES)]
        log(f"streaming {len(chunks)} packets ({CHUNK_MS} ms each)...")

        send_error: list[BaseException] = []

        def send_all() -> None:
            """Push every audio packet, pacing them like a real-time stream."""
            try:
                for index, chunk in enumerate(chunks):
                    is_last = index == len(chunks) - 1
                    ws.send(pack_audio_request(chunk, index + 2, is_last))
                    if not is_last:
                        time.sleep(CHUNK_MS / 1000)
            except BaseException as exc:  # surfaced on the main thread
                send_error.append(exc)

        sender = threading.Thread(target=send_all, daemon=True)
        sender.start()

        while True:
            try:
                frame = ws.recv()
            except (WebSocketError, OSError) as exc:
                if send_error:
                    break
                raise SystemExit(f"ASR connection error: {exc}") from exc
            if frame is None:
                break

            response = parse_response(frame)
            if response["type"] == MSG_SERVER_ERROR:
                raise SystemExit(f"ASR failed: {response['payload']}")

            text = extract_text(response["payload"])
            if text and text != transcript:
                transcript = text
                log(f"   {text}")

            if isinstance(response["payload"], dict):
                result = response["payload"].get("result")
                if isinstance(result, dict) and result.get("utterances"):
                    utterances = result["utterances"]

            # The server marks the response to the final audio packet.
            if response["is_last"]:
                break

        sender.join(timeout=args.timeout)
        if send_error:
            raise SystemExit(f"Failed to stream audio: {send_error[0]}")

    if not transcript:
        raise SystemExit("ASR returned no transcript (audio may be silent or too short)")
    return {"text": transcript, "utterances": utterances}


def emit(success: bool, error: Optional[str] = None, **fields) -> None:
    """Print the single JSON result object consumed by the agent layer."""
    print(
        json.dumps(
            {"success": success, "error": error, **fields}, ensure_ascii=False, indent=2
        )
    )


def main() -> None:
    args = parse_args()
    api_key = resolve_api_key(args.api_key)
    audio_path = Path(args.audio).expanduser()
    audio = read_wav(audio_path)
    duration = len(audio) / (ASR_SAMPLE_RATE * BYTES_PER_SAMPLE * ASR_CHANNELS)
    started = time.time()

    log("=" * 50)
    log("Ark Agent Plan ASR - doubao-seed-asr-2.0")
    log("=" * 50)
    log(f"audio    : {audio_path}")
    log(f"duration : {duration:.2f}s")
    log(f"mode     : {args.mode}")
    log("=" * 50)

    result = recognize(api_key, audio, args)
    elapsed = round(time.time() - started, 2)

    log("")
    log(f"transcript: {result['text']}")
    log(f"done in {elapsed}s")
    log("=" * 50)

    emit(
        True,
        text=result["text"],
        utterances=result["utterances"],
        metadata={
            "audio_path": str(audio_path),
            "audio_duration": round(duration, 2),
            "recognition_time": elapsed,
            "mode": args.mode,
            "model": "doubao-seed-asr-2.0",
        },
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        if exc.code not in (0, None):
            log(f"\nFailed: {exc.code}")
            emit(False, error=str(exc.code), text=None, metadata=None)
            sys.exit(1)
        raise
    except WebSocketError as exc:
        log(f"\nWebSocket error: {exc}")
        emit(False, error=str(exc), text=None, metadata=None)
        sys.exit(1)
