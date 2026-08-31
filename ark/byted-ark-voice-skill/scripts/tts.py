#!/usr/bin/env python3
"""
Ark Agent Plan TTS (Text-to-Speech) — doubao-seed-tts-2.0

Synthesises speech from text via the Agent Plan HTTP chunked streaming endpoint
and writes the audio to a local file. Emits human-readable progress on stderr
and a single JSON result object on stdout.

Usage:
    python3 scripts/tts.py --text "你好，世界" [--speaker <id>] [--format mp3]

@license MIT
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from common import TTS_HTTP_URL, TTS_RESOURCE_ID, resolve_api_key, resolve_output_dir

# Terminal status code returned by the service when synthesis finished.
CODE_FINISHED = 20000000

MAX_TEXT_LENGTH = 3000
VALID_FORMATS = ("mp3", "wav", "pcm", "ogg_opus")
# Documented sample rates for seed-tts-2.0.
VALID_SAMPLE_RATES = (8000, 16000, 24000, 32000, 44100, 48000)

DEFAULT_SPEAKER = "zh_female_vv_uranus_bigtts"

# Curated speaker presets so the agent can map natural language to a voice id.
SPEAKER_PRESETS = {
    "vv": "zh_female_vv_uranus_bigtts",
    "高冷御姐": "zh_female_gaolengyujie_uranus_bigtts",
    "邻家女孩": "zh_female_linjianvhai_moon_bigtts",
    "阳光青年": "zh_male_yangguangqingnian_moon_bigtts",
    "少年梓辛": "zh_male_shaonianzixin_moon_bigtts",
    "温柔小雅": "zh_female_wenrouxiaoya_moon_bigtts",
}


def log(message: str = "") -> None:
    """Write progress information to stderr so stdout stays machine-readable."""
    print(message, file=sys.stderr, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ark Agent Plan text-to-speech")
    parser.add_argument("--text", required=True, help="text to synthesise")
    parser.add_argument(
        "--speaker",
        default=DEFAULT_SPEAKER,
        help="voice id, or a preset name such as 高冷御姐 / 阳光青年",
    )
    parser.add_argument("--format", dest="audio_format", default="mp3")
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument(
        "--speed",
        type=float,
        default=None,
        help="speech rate multiplier, 0.5–2.0 (default: service default)",
    )
    parser.add_argument("--output", default=None, help="explicit output file path")
    parser.add_argument("--output-dir", default=None, help="output directory override")
    parser.add_argument("--api-key", dest="api_key", default=None)
    parser.add_argument(
        "--timeout", type=int, default=120, help="request timeout in seconds"
    )
    return parser.parse_args()


def validate(args: argparse.Namespace) -> None:
    """Fail fast on invalid input before spending an API call."""
    errors = []
    if not args.text.strip():
        errors.append("--text must not be empty")
    elif len(args.text) > MAX_TEXT_LENGTH:
        errors.append(
            f"--text must not exceed {MAX_TEXT_LENGTH} characters (got {len(args.text)})"
        )
    if args.audio_format not in VALID_FORMATS:
        errors.append(f"--format must be one of {'/'.join(VALID_FORMATS)}")
    if args.sample_rate not in VALID_SAMPLE_RATES:
        errors.append(f"--sample-rate must be one of {VALID_SAMPLE_RATES}")
    if args.speed is not None and not 0.5 <= args.speed <= 2.0:
        errors.append("--speed must be between 0.5 and 2.0")
    if errors:
        raise SystemExit("Parameter validation failed:\n  - " + "\n  - ".join(errors))


def resolve_speaker(speaker: str) -> str:
    """Map a friendly preset name to its voice id, passing through raw ids."""
    return SPEAKER_PRESETS.get(speaker, speaker)


def resolve_output_path(args: argparse.Namespace) -> Path:
    if args.output:
        path = Path(args.output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    ext = "ogg" if args.audio_format == "ogg_opus" else args.audio_format
    out_dir = resolve_output_dir("Ark-Voice/tts", args.output_dir)
    return out_dir / f"tts_{int(time.time())}.{ext}"


def build_payload(args: argparse.Namespace, speaker: str) -> dict:
    audio_params: dict[str, object] = {
        "format": args.audio_format,
        "sample_rate": args.sample_rate,
    }
    if args.speed is not None:
        audio_params["speech_rate"] = args.speed
    return {
        "req_params": {
            "text": args.text,
            "speaker": speaker,
            "audio_params": audio_params,
        }
    }


def synthesize(api_key: str, payload: dict, timeout: int) -> bytes:
    """Stream synthesised audio chunks and return the concatenated bytes.

    The endpoint responds with newline-delimited JSON; each line may carry a
    base64 `data` field. A non-zero `code` other than CODE_FINISHED is an error.
    """
    request = urllib.request.Request(
        TTS_HTTP_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "X-Api-Key": api_key,
            "X-Api-Resource-Id": TTS_RESOURCE_ID,
            "Content-Type": "application/json",
        },
    )

    audio = bytearray()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    # Ignore keep-alive or non-JSON padding lines.
                    continue

                code = chunk.get("code", 0)
                if code == CODE_FINISHED:
                    break
                if code:
                    raise SystemExit(
                        f"TTS failed (code {code}): {chunk.get('message', line)}"
                    )
                if chunk.get("data"):
                    audio.extend(base64.b64decode(chunk["data"]))
                    log(f"   received {len(audio) / 1024:.1f} KB")
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error: {exc.reason}") from exc

    if not audio:
        raise SystemExit("TTS failed: the service returned no audio data")
    return bytes(audio)


def emit(success: bool, error: Optional[str] = None, **fields) -> None:
    """Print the single JSON result object consumed by the agent layer."""
    print(json.dumps({"success": success, "error": error, **fields}, ensure_ascii=False,
                     indent=2))


def main() -> None:
    args = parse_args()
    validate(args)

    api_key = resolve_api_key(args.api_key)
    speaker = resolve_speaker(args.speaker)
    output_path = resolve_output_path(args)
    started = time.time()

    log("=" * 50)
    log("Ark Agent Plan TTS - doubao-seed-tts-2.0")
    log("=" * 50)
    preview = args.text if len(args.text) <= 60 else args.text[:60] + "..."
    log(f"text     : {preview}")
    log(f"speaker  : {speaker}")
    log(f"format   : {args.audio_format} @ {args.sample_rate} Hz")
    log("=" * 50)
    log("synthesising...")

    audio = synthesize(api_key, build_payload(args, speaker), args.timeout)
    output_path.write_bytes(audio)
    elapsed = round(time.time() - started, 2)

    log("")
    log(f"done in {elapsed}s -> {output_path}")
    log("=" * 50)

    emit(
        True,
        audio={
            "local_path": str(output_path),
            "size_bytes": len(audio),
            "format": args.audio_format,
            "sample_rate": args.sample_rate,
        },
        metadata={
            "text": args.text,
            "speaker": speaker,
            "generation_time": elapsed,
            "model": "doubao-seed-tts-2.0",
            "save_dir": str(output_path.parent),
        },
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        # Surface a structured failure so the agent layer can react uniformly.
        if exc.code not in (0, None):
            log(f"\nFailed: {exc.code}")
            emit(False, error=str(exc.code), audio=None, metadata=None)
            sys.exit(1)
        raise
