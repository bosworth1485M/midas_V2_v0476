# scripts/patch_strategy_v048.py
"""
Minimal, safe v0.4.8 patch for strategy.py:
- Restores from strategy.bak.py if you want to start fresh (optional).
- Inserts ONE import for the micro gateway (tagged # v0.4.8).
- Inserts ONE guarded micro block just before the final 'return True' in should_enter (tagged # v0.4.8).
Never edits anything else.
"""
from pathlib import Path

STRAT = Path(r"C:\Users\boydp\Desktop\midas_V2_v047_working\src\midas_v2\strategy.py")
BAK   = Path(r"C:\Users\boydp\Desktop\midas_V2_v047_working\src\midas_v2\strategy.bak.py")
TAG   = "# v0.4.8"

IMPORT_LINE = "from midas_v2.micro.micro_gateway import check_micro_continuation  # v0.4.8\n"

BLOCK = (
    "            # Micro continuation (5s/1s) - only if enabled  # v0.4.8\n"
    "            if self.p.use_micro_confirmation or self.p.require_micro_continuation:  # v0.4.8\n"
    "                sym = getattr(self, \"symbol\", None)  # v0.4.8\n"
    "                if not sym:  # v0.4.8\n"
    "                    return False  # v0.4.8\n"
    "\n"
    "                ts = int(getattr(bars[i], \"ts\", getattr(bars[i], \"t\", 0)))  # v0.4.8\n"
    "                ok = check_micro_continuation(  # v0.4.8\n"
    "                    symbol=sym,  # v0.4.8\n"
    "                    minute_close_epoch=ts,  # v0.4.8\n"
    "                    resolution=(self.p.micro_resolution or \"5s\"),  # v0.4.8\n"
    "                    window_secs=int(self.p.micro_window_secs or 60),  # v0.4.8\n"
    "                    require_ema=bool(self.p.micro_require_ema_reclaim),  # v0.4.8\n"
    "                    require_vwap=bool(self.p.micro_require_vwap_hold),  # v0.4.8\n"
    "                    min_green_ratio=float(self.p.micro_min_green_ratio or 0.60),  # v0.4.8\n"
    "                    allow_first_pullback=bool(self.p.micro_allow_first_pullback),  # v0.4.8\n"
    "                )  # v0.4.8\n"
    "                if not ok:  # v0.4.8\n"
    "                    return False  # v0.4.8\n"
)

def insert_import(text: str) -> str:
    if IMPORT_LINE.strip() in text:
        return text
    # insert after the typing import line if present, else after first import block
    lines = text.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.strip() == "from typing import List, Optional":
            lines.insert(i+1, IMPORT_LINE + "\n")
            return "".join(lines)
    # fallback: place after first line
    lines.insert(1, IMPORT_LINE + "\n")
    return "".join(lines)

def insert_block_before_final_return(text: str) -> str:
    if "check_micro_continuation(" in text:
        return text  # already patched
    # find the last 'return True' inside should_enter
    start = text.find("def should_enter(")
    if start == -1:
        return text
    idx = text.rfind("\n        return True", start)  # 8 spaces then return True
    if idx == -1:
        return text
    return text[:idx] + "\n" + BLOCK + text[idx:]

def main():
    if not STRAT.exists():
        print(f"[ERROR] Not found: {STRAT}")
        return
    src = STRAT.read_text(encoding="utf-8")
    # save a pre-patch backup next to strategy.py
    pre = STRAT.with_name("strategy.pre_v048.py")
    pre.write_text(src, encoding="utf-8")

    # apply minimal patch
    patched = insert_import(src)
    patched = insert_block_before_final_return(patched)

    if patched == src:
        print("[INFO] No changes applied (already patched or anchors not found).")
        return

    STRAT.write_text(patched, encoding="utf-8")
    print("[OK] strategy.py patched. Backup:", pre)

if __name__ == "__main__":
    main()