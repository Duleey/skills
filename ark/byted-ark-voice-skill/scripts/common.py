"""
Common utilities for Ark Agent Plan Voice Skill.

Provides:
- API Key auto-detection (3-tier priority strategy)
- Output directory resolution with graceful degradation
- Shared constants for TTS / ASR endpoints

@license MIT
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================
# Constants
# ============================================

# TTS endpoints (Agent Plan dedicated paths)
TTS_HTTP_URL = "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional"
TTS_WS_UNIDIRECTIONAL_URL = (
    "wss://openspeech.bytedance.com/api/v3/plan/tts/unidirectional/stream"
)
TTS_WS_BIDIRECTIONAL_URL = (
    "wss://openspeech.bytedance.com/api/v3/plan/tts/bidirection"
)

# ASR endpoints (Agent Plan dedicated paths)
ASR_WS_ASYNC_URL = "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_async"
ASR_WS_NOSTREAM_URL = (
    "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream"
)

# Resource IDs required by the X-Api-Resource-Id header
TTS_RESOURCE_ID = "seed-tts-2.0"
ASR_RESOURCE_ID = "volc.seedasr.sauc.duration"

# ASR requires 16kHz / 16bit / mono PCM
ASR_SAMPLE_RATE = 16000
ASR_BITS = 16
ASR_CHANNELS = 1

HOME = Path.home()


# ============================================
# API Key detection
# ============================================


def validate_ark_key(key: Optional[str]) -> Optional[str]:
    """Return the trimmed key when it is a valid Agent Plan key, else None."""
    if not key or not isinstance(key, str):
        return None
    trimmed = key.strip()
    return trimmed if trimmed.startswith("ark-") else None


def detect_platform() -> str:
    """Identify the host agent platform to read its config file."""
    if (HOME / ".openclaw").exists():
        return "openclaw"
    if (HOME / ".hermes").exists():
        return "hermes"
    if (HOME / ".claude").exists() or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "claude-code"
    return "unknown"


def _find_openclaw_key() -> Optional[str]:
    config_path = HOME / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        return None
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    providers = (config.get("models") or {}).get("providers") or {}
    for provider in providers.values():
        if isinstance(provider, dict):
            key = validate_ark_key(provider.get("apiKey"))
            if key:
                return key
    return None


def _find_hermes_key() -> Optional[str]:
    config_path = HOME / ".hermes" / "config.yaml"
    if not config_path.exists():
        return None
    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"api_key:\s*[\"']?(ark-[^\"'\s]+)", content)
    return validate_ark_key(match.group(1)) if match else None


def _find_claude_code_key() -> Optional[str]:
    # Session environment variable takes precedence over the config file.
    key = validate_ark_key(os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    if key:
        return key
    config_path = HOME / ".claude" / "settings.json"
    if not config_path.exists():
        return None
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return validate_ark_key((config.get("env") or {}).get("ANTHROPIC_AUTH_TOKEN"))


def _scan_env_for_key() -> Optional[str]:
    """Fallback: scan common environment variable names for an ark- key."""
    for name in (
        "ARK_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "API_KEY",
        "API_Key",
        "api_key",
        "apiKey",
    ):
        key = validate_ark_key(os.environ.get(name))
        if key:
            return key
    return None


def resolve_api_key(cli_key: Optional[str] = None) -> str:
    """Resolve the Agent Plan API key using a 3-tier priority strategy.

    Priority: CLI argument > current platform config > environment scan.
    Raises SystemExit with actionable guidance when nothing is found.
    """
    if cli_key:
        key = validate_ark_key(cli_key)
        if not key:
            raise SystemExit(
                'API Key must start with "ark-" (Agent Plan dedicated format)'
            )
        return key

    platform = detect_platform()
    finder = {
        "openclaw": _find_openclaw_key,
        "hermes": _find_hermes_key,
        "claude-code": _find_claude_code_key,
    }.get(platform)
    if finder:
        key = finder()
        if key:
            return key

    key = _scan_env_for_key()
    if key:
        return key

    raise SystemExit(
        "No valid Agent Plan API Key found.\n"
        "Send an API Key starting with 'ark-' in the conversation, "
        "or pass it via --api-key."
    )


# ============================================
# Output path resolution
# ============================================


def resolve_output_dir(sub_dir: str, override: Optional[str] = None) -> Path:
    """Resolve the output directory with a 3-tier degradation strategy.

    Priority: explicit override / env var > Desktop > home directory > cwd.
    A date-based sub-directory keeps generated files organised.
    """
    base: Optional[Path] = None
    candidate = override or os.environ.get("ARK_VOICE_SAVE_PATH")
    if candidate:
        base = Path(candidate).expanduser()
    elif (HOME / "Desktop").exists():
        base = HOME / "Desktop" / sub_dir
    elif HOME.exists():
        base = HOME / sub_dir
    else:
        base = Path.cwd() / sub_dir

    target = base / datetime.now().strftime("%Y-%m-%d")
    target.mkdir(parents=True, exist_ok=True)
    return target
