#!/usr/bin/env python3
"""
clear_comparisons.py

Deletes all files inside every `_comparisons` folder under ./out/YYYYMMDD/.
"""

from pathlib import Path

def main():
    root = Path("out")
    if not root.exists():
        print("[ERROR] No 'out' folder found in current directory.")
        return

    targets = list(root.glob("*\\_comparisons\\*"))

    if not targets:
        print("[INFO] No comparison files found.")
        return

    print(f"[INFO] Deleting {len(targets)} comparison files...")
    for fp in targets:
        try:
            fp.unlink()
            print("  deleted", fp)
        except Exception as e:
            print(f"  [ERROR] Could not delete {fp}: {e}")

    print("[DONE] All comparison files cleared.")

if __name__ == "__main__":
    main()