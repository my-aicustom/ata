#!/usr/bin/env python3
"""ATA local preflight: code/dependency/storage checks only; no paid provider call."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from core.preflight import runtime_preflight


def main() -> int:
    result=runtime_preflight()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('code_ready') else 1


if __name__=='__main__':
    raise SystemExit(main())
