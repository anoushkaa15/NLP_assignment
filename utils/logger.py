"""Small colorized logger for terminal-friendly demo output."""

from __future__ import annotations

import json
from typing import Any


class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def info(message: str) -> None:
    print(f"{Colors.BLUE}▶ {message}{Colors.RESET}")


def success(message: str) -> None:
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def warning(message: str) -> None:
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def error(message: str) -> None:
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_json_preview(label: str, data: Any, max_chars: int = 1200) -> None:
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n..."
    print(f"{Colors.BOLD}{label}{Colors.RESET}\n{text}\n")
