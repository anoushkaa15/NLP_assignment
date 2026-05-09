"""Shared state helpers for the multi-step fact-checking chain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def create_initial_state(user_input: str) -> dict[str, Any]:
    """Create the assignment-required shared dictionary state."""

    return {
        "user_input": user_input,
        "claims": {},
        "evidence": [],
        "evidence_quality": {},
        "analysis": {},
        "credibility": {},
        "final_report": "",
        "errors": [],
        "trace": [],
    }


def record_step(state: dict[str, Any], step_name: str, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
    """Store trace information so each chain dependency can be inspected live."""

    state["trace"].append(
        {
            "step": step_name,
            "input_keys": sorted(inputs.keys()),
            "output_keys": sorted(outputs.keys()),
            "inputs": inputs,
            "outputs": outputs,
        }
    )


def save_state_json(state: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def save_report_markdown(report: str, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


def print_step_debug(step_name: str, outputs: dict[str, Any]) -> None:
    """Print readable intermediate outputs during execution."""

    print(f"\n===== {step_name} =====")
    print(json.dumps(outputs, indent=2, ensure_ascii=False)[:4000])
