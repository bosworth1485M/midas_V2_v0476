#!/usr/bin/env python3
import argparse, datetime, os, re, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def first_docline(p: Path) -> str:
    t = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'^\s*"""(.*?)"""', t, re.S|re.M) or re.search(r"^\s*'''(.*?)'''", t, re.S|re.M)
    if not m: return ""
    return re.sub(r"\s+", " ", (m.group(1).strip().splitlines() or [""])[0])[:140]

def build_scripts_index() -> str:
    rows=[]
    for p in sorted((ROOT/"scripts").glob("*.py"), key=lambda x:x.name.lower()):
        rows.append(f"- `scripts/{p.name}` — {first_docline(p) or 'no docstring'}")
    return "# SCRIPTS_INDEX\n\n" + "\n".join(rows) + "\n"

def build_user_guide() -> str:
    return textwrap.dedent("""
    # USER_GUIDE

    ## Catalyst Hybrid — Single Day (B baseline)
    ```powershell
    python scripts/run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
    ```

    ## Catalyst Hybrid — Date Range (B baseline)
    ```powershell
    python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
    ```

    ### Outputs
    - Kept news: `data/catalyst/catalyst_only_<DATE>.txt`
    - Hybrid: `data/catalyst/universe_hybrid_<DATE>.txt`
    - Results: `out/<YYYYMMDD>/B_hybrid/results_<DATE>.csv`
    - Summaries: `summary_hybrid_<DATE>.txt`, `run_summary.(txt|csv)`

    ### What the runner prints
    - `[PREFLIGHT]` band (min=10, max=40)
    - `[FILTER] enforce-band removed …`
    - `[RUN SUMMARY]` line
    - Per-symbol table with `included_by`, `news_score`, `in_band`, and **Type** (`standard` / `rocket`)
    """).strip()+"\n"

def build_dev_guide(version: str) -> str:
    today = datetime.date.today().isoformat()
    return textwrap.dedent(f"""
    # DEV_GUIDE

    ## Version
    - Current tag: **{version}**
    - Updated: {today}

    ## Catalyst Hybrid — Single Day (B baseline)
    ```powershell
    python scripts/run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
    ```

    ## Catalyst Hybrid — Date Range (B baseline)
    ```powershell
    python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
    ```

    ### Notes
    - Wrapper passes the **full RAW file** to compose (reliable hybrid fill).
    - Compose builds **news + RAW fillers**; run-day applies junk-class → news-first → Top-N → **10–40% band** (B).

    ### Gotcha
    Compose expects **full RAW path** for `--raw` (e.g., `data/raw/universe_topgappers_<DATE>.txt`).
    Using a prefix may produce `rawTop=0` (news-only).

    """).strip()+"\n"

def maybe_include_commands() -> str:
    # If you keep a single “commands” doc, include it as an appendix automatically.
    for p in [
        ROOT/"Docs/Midas_Backtesting_Commands.md",
        ROOT/"Docs/Test Commands/Midas_Backtesting_Commands_v1.2.md",
        ROOT/"Docs/Test Commands/Midas_Backtesting_Commands.md",
    ]:
        if p.exists():
            return "\n\n---\n\n## Appendix: Commands Reference\n\n"+p.read_text(encoding="utf-8")
    return ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=os.environ.get("MIDAS_VERSION","v0.3.31"))
    args = ap.parse_args()

    (ROOT/"SCRIPTS_INDEX.md").write_text(build_scripts_index(), encoding="utf-8")
    (ROOT/"USER_GUIDE.md").write_text(build_user_guide(), encoding="utf-8")
    dev = build_dev_guide(args.version) + maybe_include_commands()
    (ROOT/"DEV_GUIDE.md").write_text(dev, encoding="utf-8")
    print("Docs refreshed: SCRIPTS_INDEX.md, USER_GUIDE.md, DEV_GUIDE.md")

if __name__ == "__main__":
    main()