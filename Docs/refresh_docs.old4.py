# Docs/refresh_docs.py
# Purpose: Refresh docs under Docs/, inject Scripts Inventory, Run-Day sections,
# Catalyst Hybrid sections, sync DEV_GUIDE scenario tables, and auto-fix unclosed
# ``` code fences. Markdown only; no PDF export; single-write per file with clear logs.

import json, re, sys, time
from pathlib import Path
from typing import List, Tuple

# ---------------- Config ------------------------------------------------------

REQUIRED_SCRIPTS = [
    "scripts/run_day_simple.py",
    "scripts/summarize_results.py",
    "scripts/topgappers.py",
    "scripts/fetch_minutes_polygon.py",
    "scripts/run_all_scenarios.ps1",
]

SCRIPT_EXTENSIONS   = {".py", ".ps1", ".cmd", ".bat"}
IGNORE_SUBSTRINGS   = {".git", "venv", "__pycache__"}
GUIDES_TO_TOUCH     = ["Docs/USER_GUIDE.md", "Docs/DEV_GUIDE.md"]
USER_GUIDE_PATH     = "Docs/USER_GUIDE.md"
DEV_GUIDE_PATH      = "Docs/DEV_GUIDE.md"
SCRIPTS_INDEX_FILE  = "Docs/SCRIPTS_INDEX.md"
INVENTORY_SECTION_TITLE = "## Scripts Inventory (auto)"

# ---------------- New hybrid flow snippets -----------------------------------

HYBRID_SNIPPETS = [
    ("## Catalyst Hybrid — Single Day (auto)",
     None,
     "```powershell\n"
     "python scripts/run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band\n"
     "```\n\n"
     "**What this does**\n"
     "- Uses **news-first** selection; fills with RAW gappers up to **Top-12** within the enforce-band (price/gap).\n"
     "- Wrapper passes the **full RAW file path** to compose; compose builds **news + RAW fillers**.\n"
     "- Runs Scenario **B** on the hybrid universe."),

    ("## Catalyst Hybrid — Date Range (auto)",
     None,
     "```powershell\n"
     "python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band\n"
     "```\n\n"
     "**Notes**\n"
     "- Consider enabling an **opening RVOL gate** in config/scenarios.json (e.g., ≥1.5× first 10–15m vs prior day).\n"
     "- Optional headline polarity filter in `enrich_universe_catalyst.py` (e.g., `--deny-negative` with `data/catalyst/neg_terms.txt`)."),

    ("### Catalyst Hybrid Notes (auto)",
     None,
     "- Compose expects **full RAW path** for `--raw`, e.g. `data/raw/universe_topgappers_<DATE>.txt`.\n"
     "- Using a prefix may produce `rawTop=0` (news-only)."),
]

# Existing run-day sections (kept from your working script)
RUN_DAY_SNIPPETS = [
    ("## Run-Day Success Sequence (auto)", "Docs/sections/run_day_success.md",
     "### Overview\n"
     "This section documents the *successful* sequence after running:\n"
     "`python scripts/run_day_simple.py --date YYYY-MM-DD --scenario B`\n\n"
     "1. **Top gappers fetched** (Polygon or your source)\n"
     "2. **Universe file written** (e.g., `data/samples/universe_sample.txt`)\n"
     "3. **Minute data fetched** into `data/...`\n"
     "4. **Backtest runs** for chosen scenario; results to `out/<YYYYMMDD>/<Scenario>/results_YYYY-MM-DD.csv`\n"
     "5. **Summarize** via `python scripts/summarize_results.py --date YYYY-MM-DD`\n\n"
     "> Edit `Docs/sections/run_day_success.md` to keep this aligned with your exact outputs.\n"),
    ("## Run-Day Errors & Debugging (auto)", "Docs/sections/run_day_debug.md",
     "### Quick checks\n"
     "- Run `python scripts/run_day_simple.py --help` to ensure argparse is intact\n"
     "- Confirm required files are present (see Scripts Inventory banner above)\n"
     "- If data is missing for the prior trading day, check your data fetch or market calendar logic\n"
     "- Inspect logs/console output for `[ERR]` lines\n\n"
     "### Common issues\n"
     "- **No results CSV**: verify universe symbols and minute data are present\n"
     "- **Empty CSV**: strategy filters may be too strict; confirm scenario config\n\n"
     "> Edit `Docs/sections/run_day_debug.md` to add your specific error cases and remedies.\n"),
]

# ---------------- Helpers -----------------------------------------------------

def log(msg: str):
    print(msg, flush=True)

def err(msg: str):
    print(msg, file=sys.stderr, flush=True)

def _finalize_markdown(md_text: str) -> str:
    count = md_text.count("```")
    if count % 2 == 1:
        if not md_text.endswith("\n"):
            md_text += "\n"
        md_text += "```\n"
    if not md_text.endswith("\n"):
        md_text += "\n"
    return md_text

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except Exception as e:
        err(f"[WARN] Could not read {path}: {e}")
        return ""

def write_if_changed(path: Path, original: str, new_text: str) -> bool:
    new_final = _finalize_markdown(new_text)
    if new_final != original:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_final, encoding="utf-8")
        log(f"[Docs] Wrote {path}")
        return True
    else:
        log(f"[Docs] No changes in {path}")
        return False

def is_ignored(p: Path) -> bool:
    s = p.as_posix().lower()
    return any(tok in s for tok in IGNORE_SUBSTRINGS)

# ---------------- Scripts Index + Required Check ------------------------------

def generate_scripts_index(root: Path, out_path: Path) -> Tuple[str, List[str]]:
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SCRIPT_EXTENSIONS and not is_ignored(p):
            files.append(p)

    lines = [
        "# Script Index",
        "",
        "(auto-generated by refresh_docs.py; do not edit by hand)",
        "",
    ]
    for p in sorted(files, key=lambda x: x.as_posix().lower()):
        rel = p.relative_to(root).as_posix()
        try:
            with open(p, "r", errors="ignore", encoding="utf-8") as fh:
                first = (fh.readline() or "").strip()
        except Exception:
            first = ""
        mtime = time.strftime("%Y-%m-%d", time.localtime(p.stat().st_mtime))
        lines.append(f"- `{rel}` — {mtime} — {first[:160]}")

    md = "\n".join(lines)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_finalize_markdown(md), encoding="utf-8")
    log(f"[Docs] Wrote {out_path}")

    missing: List[str] = [r for r in REQUIRED_SCRIPTS if not (root / r).exists()]
    return md, missing

def inject_inventory_section(doc_md: str, scripts_index_md: str, missing: List[str]) -> str:
    banner = "> Required scripts: **All present**" if not missing else "> **Missing scripts:** " + ", ".join(missing)
    section = f"\n{INVENTORY_SECTION_TITLE}\n{banner}\n\n{scripts_index_md}\n"

    if INVENTORY_SECTION_TITLE in doc_md:
        pattern = re.compile(
            rf"{re.escape(INVENTORY_SECTION_TITLE)}.*?(?=\n## |\Z)",
            flags=re.DOTALL | re.IGNORECASE,
        )
        if pattern.search(doc_md):
            doc_md = pattern.sub(lambda m: section.strip() + "\n", doc_md)
        else:
            doc_md = doc_md.rstrip() + "\n" + section
    else:
        doc_md = doc_md.rstrip() + "\n" + section

    return doc_md

# ---------------- Section injection utilities ---------------------------------

def load_snippet_or_default(root: Path, rel_path: str, default_text: str) -> str:
    if rel_path:
        p = root / rel_path
        if p.exists():
            return read_text(p)
    return default_text

def inject_or_replace_section(doc_md: str, title: str, body_md: str) -> str:
    section = f"\n{title}\n\n{body_md.strip()}\n"
    if title in doc_md:
        pattern = re.compile(rf"{re.escape(title)}.*?(?=\n## |\Z)", flags=re.DOTALL | re.IGNORECASE)
        if pattern.search(doc_md):
            return pattern.sub(lambda m: section.strip() + "\n", doc_md)
    return doc_md.rstrip() + "\n" + section

def ensure_user_guide_exists(root: Path, path: Path):
    if not path.exists():
        skeleton = (
            "# USER GUIDE\n\n"
            "This guide explains how to run and validate daily backtests, where outputs are written,\n"
            "and how to debug common issues.\n\n"
            "*(This file was created automatically by refresh_docs.py. Feel free to edit.)*\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_finalize_markdown(skeleton), encoding="utf-8")
        log(f"[Docs] Wrote {path}")

def ensure_dev_guide_exists(root: Path, path: Path):
    if not path.exists():
        skeleton = (
            "# DEV GUIDE\n\n"
            "Engineering-facing notes for scenarios, configs, and runners.\n\n"
            "*(This file was created automatically by refresh_docs.py. Feel free to edit.)*\n"
            "\n## Sections\n\n"
            "### Scenario presets (summary view)\n\n"
            "| Scenario | tp_pct | sl_pct | ema_confirm | vwap_confirm | macd_confirm | dip_reclaim | min_dip_pct | min_reclaim_pct | reclaim_ref | ema_period | gate_minutes | rise_bars | min_pm_vol |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n\n"
            "### Scenario presets from config/scenarios.json\n\n"
            "| Scenario | Source | Params (JSON) |\n"
            "|---|---|---|\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_finalize_markdown(skeleton), encoding="utf-8")
        log(f"[Docs] Wrote {path}")

def inject_user_guide_sections(root: Path, user_guide_md: str) -> str:
    updated = user_guide_md
    for (title, rel_path, default_text) in RUN_DAY_SNIPPETS:
        body = load_snippet_or_default(root, rel_path, default_text)
        updated = inject_or_replace_section(updated, title, body)
    for (title, rel_path, default_text) in HYBRID_SNIPPETS[:2]:
        body = load_snippet_or_default(root, rel_path, default_text)
        updated = inject_or_replace_section(updated, title, body)
    return updated

def maybe_include_commands(root: Path) -> str:
    for p in [
        Path("Docs/Midas_Backtesting_Commands.md"),
        Path("Docs/Test Commands/Midas_Backtesting_Commands_v1.2.md"),
        Path("Docs/Test Commands/Midas_Backtesting_Commands.md"),
    ]:
        if p.exists():
            return "\n\n---\n\n## Appendix: Commands Reference\n\n" + read_text(p)
    return ""

# ---------------- DEV_GUIDE Scenario Sync (pure-transform) -------------------

SCENARIO_TABLE_HEADER = (
    "| Scenario | tp_pct | sl_pct | ema_confirm | vwap_confirm | macd_confirm | dip_reclaim | min_dip_pct | min_reclaim_pct | reclaim_ref | ema_period | gate_minutes | rise_bars | min_pm_vol |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
)

def build_scenario_table_rows(params: dict, name: str) -> str:
    def get(k, default=None): return params.get(k, default)
    row = [
        name,
        str(get("tp_pct","")),
        str(get("sl_pct","")),
        str(get("ema_confirm","")),
        str(get("vwap_confirm","")),
        str(get("macd_confirm","")),
        str(get("dip_reclaim","")),
        str(get("min_dip_pct","")),
        str(get("min_reclaim_pct","")),
        str(get("reclaim_ref","")),
        str(get("ema_period","")),
        str(get("gate_minutes","")),
        str(get("rise_bars","")),
        str(get("min_pm_vol","")),
    ]
    return "| " + " | ".join(row) + " |"

def sync_dev_guide_scenarios_text(root: Path, dev_text: str) -> str:
    cfg_path = root / "config" / "scenarios.json"
    try:
        data = json.loads(read_text(cfg_path)) if cfg_path.exists() else {}
    except Exception:
        data = {}

    ordered = [k for k in ["A","B","C","D","E"] if k in data]

    if ordered:
        table_rows = [SCENARIO_TABLE_HEADER]
        for key in ordered:
            table_rows.append(build_scenario_table_rows(data[key]["params"], key))
        table_block = "\n".join(table_rows) + "\n\n"

        json_header = "| Scenario | Source | Params (JSON) |\n|---|---|---|"
        json_rows = []
        for key in ordered:
            json_rows.append(f'| {key} | config\\scenarios.json | {json.dumps(data[key]["params"], separators=(",",":"))} |')
        json_block = json_header + "\n" + "\n".join(json_rows) + "\n\n"

        dev_text = re.sub(
            r"(### Scenario presets \(summary view\)\s*\n\n)(?:\|[^\n]*\n\|[-\|]+\n(?:.*\n)+?)",
            lambda m: m.group(1) + table_block,
            dev_text, flags=re.DOTALL
        )
        dev_text = re.sub(
            r"(### Scenario presets from config/scenarios\.json\s*\n\n)(?:\|[^\n]*\n\|[-\|]+\n(?:.*\n)+?)",
            lambda m: m.group(1) + json_block,
            dev_text, flags=re.DOTALL
        )

    hybrid_notes = HYBRID_SNIPPETS[2][2]
    dev_text = inject_or_replace_section(dev_text, HYBRID_SNIPPETS[2][0], hybrid_notes)
    return dev_text

# ---------------- Main --------------------------------------------------------

def main():
    root = Path(".").resolve()
    docs_dir = root / "Docs"
    if not docs_dir.exists():
        err(f"[ERR] Docs folder not found at {docs_dir}. Create it first.")
        sys.exit(1)

    log(f"[Docs] Using repo root: {root}")

    # 1) Scripts Index + Required Check
    scripts_index_path = root / SCRIPTS_INDEX_FILE
    scripts_index_md, missing = generate_scripts_index(root, scripts_index_path)

    # 2) USER_GUIDE: ensure exists, then compute all changes and write once
    ug_path = root / USER_GUIDE_PATH
    if not ug_path.exists():
        ensure_user_guide_exists(root, ug_path)
    ug_original = read_text(ug_path)
    ug_step1 = inject_inventory_section(ug_original, read_text(scripts_index_path), missing)
    ug_step2 = inject_user_guide_sections(root, ug_step1)
    write_if_changed(ug_path, ug_original, ug_step2)

    # 3) DEV_GUIDE: ensure exists, then compute all changes and write once
    dg_path = root / DEV_GUIDE_PATH
    if not dg_path.exists():
        ensure_dev_guide_exists(root, dg_path)
    dg_original = read_text(dg_path)
    dg_step1 = inject_inventory_section(dg_original, read_text(scripts_index_path), missing)
    dg_step2 = sync_dev_guide_scenarios_text(root, dg_step1)
    dg_step3 = dg_step2 + maybe_include_commands(root)
    write_if_changed(dg_path, dg_original, dg_step3)

    # 4) Final status
    if missing:
        err(f"[WARN] Missing required scripts: {', '.join(missing)}")
        sys.exit(2)
    log("[OK] Refresh complete; required scripts present.")
    sys.exit(0)

if __name__ == "__main__":
    main()
