# Handover Document — Transition from v0.8.1.15.0 to v0.8.1.16.0

## Use this document at the **start of the next version thread** to restore full context.

---

## 1. Where v0.8.1.15.0 Ended (Authoritative Summary)

v0.8.1.15.0 was a **pure diagnostic version**. No strategy logic, guards, parameters, or execution behavior were changed.

The version answered the following question conclusively:

> **Are executed SL trades caused by a failing guard?**

### Final Answer

**No.**

* All guards fired correctly and aggressively.
* VWAP_EXT, STRUCT_DAMAGE, DAY_GATE, and MAX_TRADES_PER_SYMBOL behaved as designed.
* Executed trades occurred only after *all* guards passed.
* There was no contradiction between:

  * runtime guard decisions,
  * TWCS structure,
  * and logged `[WHY]` output.

Losses observed were a mix of:

* **Loss Class A (2 examples)** — plausible but unproven entry-structure weakness
* **Loss Class B (≥3 examples)** — structurally valid entries that still failed (normal trade risk)

Because Loss Class A appeared only **twice**, no new guard was justified.

v0.8.1.15.0 is therefore **complete, closed, and correct**.

---

## 2. Critical Logging Rule (DO NOT SKIP)

### Why this matters

During v0.8.1.15.0, it was confirmed that:

* Guard / `[WHY]` / DAY_GATE / VWAP_EXT / STRUCT_DAMAGE logs are emitted via **Python logging to stderr**.
* PowerShell `Tee-Object` captures **stdout only by default**.

If stderr is not captured, guard output will:

* appear on screen
* **but not** be written to the runlog file

This is **not a logic issue** — it is a stream-capture detail.

### Mandatory run pattern for v0.8.1.16.0

All diagnostic runs **must** use:

```
python <command> 2>&1 | Tee-Object out\auto\<runlog>.txt
```

Failure to do this invalidates the run for diagnostic purposes.

---

## 3. What Was Learned in v0.8.1.15.0 (Carry-Forward Findings)

### Loss Class A — *Late VWAP Re-push After Stall* (2 examples)

**Examples:** BIYA (2025-11-06), BNAI (2025-11-10)

**Structural Signature:**

* Entry already extended above VWAP
* `green_streak = 1`
* Entry on a **late re-push**, not the first impulse
* Clear stall / overlap immediately before entry
* No base or consolidation

This class is **plausibly guardable**, but currently **below the ≥3 threshold**.

---

### Loss Class B — *Structurally Valid Continuation That Failed* (≥3 examples)

**Examples:** AMIX, WTO, SGML (2025-11-17)

**Structural Signature:**

* `green_streak ≥ 2`
* Multi-bar continuation
* Base or coil present
* Entry not late

These losses are **normal trade risk** and should not be blocked.

---

## 4. Objective of v0.8.1.16.0 (Option A — ACCEPTED)

### Primary Objective

> **Continue executed-loss diagnosis until Loss Class A either reaches ≥3 independent examples or is shown to remain rare across regimes.**

This version is still **diagnostic-only**.

### What v0.8.1.16.0 Is Allowed to Do

* Run additional loss-rich days or ranges
* Analyze SL trades using TWCS and full guard logs
* Count occurrences of Loss Class A precisely

### What v0.8.1.16.0 Is NOT Allowed to Do

* No guard enforcement
* No blocking logic
* No parameter changes
* No “soft” filters
* No speculative fixes

---

## 5. Recommended Ranges to Run in v0.8.1.16.0

The goal is to **maximize SL density** while staying in comparable regimes and avoiding unnecessary noise.

### Single Best Starting Sub-Range (RECOMMENDED)

**Start with the following focused sub-range:**

```
python scripts\run_range_and_summarize.py --start 2025-11-18 --end 2025-11-22 --scenario B 2>&1 | Tee-Object out\\auto\\B_runlog_20251118_20251122_v0.8.1.16.0.txt
```

#### Why this is the best starting range

* It is **adjacent in time** to the already-analyzed Nov-17 loss cluster
* Market regime is likely similar (no large structural regime break)
* High probability of **loss-rich days** without jumping too far forward
* Small enough to inspect trade-by-trade without fatigue
* Preserves causality: we are extending the same environment, not switching contexts

This range is expected to either:

* produce a **3rd Loss Class A** example (promotion candidate), or
* demonstrate that Loss Class A remains **rare and non-systematic**

### Secondary Ranges (ONLY if needed)

Run these **only if** the primary sub-range does not resolve the question.

#### Secondary Range A — Remainder of November 2025

```
python scripts\run_range_and_summarize.py --start 2025-11-25 --end 2025-11-30 --scenario B 2>&1 | Tee-Object out\\auto\\B_runlog_20251125_20251130_v0.8.1.16.0.txt
```

#### Secondary Range B — Earlier Hostile Regime (Control)

```
python scripts\run_range_and_summarize.py --start 2025-07-14 --end 2025-07-18 --scenario B 2>&1 | Tee-Object out\\auto\\B_runlog_20250714_20250718_v0.8.1.16.0.txt
```

Only proceed to secondary ranges if the primary sub-range does **not** produce a decisive outcome.

---

## 6. How to Analyze Each Run (Exact Steps)

### Step 1 — Identify SL trades

```
Select-String -Path out\YYYYMMDD\B\results_YYYY-MM-DD.csv -Pattern ",SL," | ForEach-Object { $_.Line }
```

### Step 2 — Locate TWCS snapshots

```
out\YYYYMMDD\B\<SYMBOL>\snapshots\<TRADE_ID>\
```

Review:

* `trade_snapshot_entry.png`
* `trade_snapshot_entry_meta.json`

### Step 3 — Check structural signature

For each SL trade, answer:

* Was entry extended above VWAP?
* Was `green_streak == 1`?
* Was there a stall / overlap immediately before entry?
* Was entry a late re-push?

### Step 4 — Verify guard behavior

Search the runlog:

```
Select-String -Path out\auto\<runlog>.txt -Pattern "\[WHY\]|VWAP_EXT|STRUCT_DAMAGE|DAY_GATE" | Select-Object -First 200
```

Confirm:

* Guards passed for the executed trade
* No contradiction with TWCS

---

## 7. Promotion Rule (Strict)

A new guard may be proposed **only if**:

* Loss Class A appears **≥3 times** across independent symbols/days
* Structural signature matches *exactly*
* Guard logic can be expressed as **one narrow rule**

If these conditions are not met:

* v0.8.1.16.0 ends with **no changes**

---

## 8. Expected Outcomes

### Valid End States

* **Outcome A:** 3rd Loss Class A found → propose single narrow guard in v0.8.1.17.0
* **Outcome B:** Loss Class A remains rare → document and abandon as non-material

Both outcomes are success.

---

## 9. Final Instruction to the Next Version

Do **not** rush to fix.

This system is already well-guarded.
The task of v0.8.1.16.0 is to **count carefully**, not to improve prematurely.

---

*End of Handover Document — Start v0.8.1.16.0 here.*
