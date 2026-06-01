"""ABM-Microstructure 実験A harness。

公開 API: `run(SimConfig) -> RunResult`。検証アンカーは `anchors`。
"""
from __future__ import annotations

from .config import SimConfig
from .engine import RunResult, measure_competitive_spread, run

__all__ = ["SimConfig", "RunResult", "run", "measure_competitive_spread"]
