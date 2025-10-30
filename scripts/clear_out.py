#!/usr/bin/env python3
import shutil, os
from pathlib import Path

out_dir = Path(__file__).resolve().parents[1] / "out"
if out_dir.exists():
    shutil.rmtree(out_dir)
out_dir.mkdir(parents=True, exist_ok=True)
print("[OK] out/ cleared and recreated.")