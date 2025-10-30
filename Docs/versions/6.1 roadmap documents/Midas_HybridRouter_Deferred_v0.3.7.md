# Hybrid Router (A–E) — Deferred

**Date:** 2025-09-07  
**Status:** Deferred (post‑tuning)  
**Version context:** v0.3.7-cleanup  

---

## Rationale
We will postpone introducing a Scenario Router (hybrid of A–E) until we finish **tuning and validating** the individual scenarios. Early hybridization could mask weaknesses in B/D/E and make debugging harder.

---

## Prerequisites Before Hybridization
- ✅ Clean repo checkpoint at **v0.3.7-cleanup**  
- ☐ Re‑establish **Scenario B** as a stable baseline (Aug + Sep)  
- ☐ Validate **Scenario D_strict** across Aug + Sep (target ~60–63% WR)  
- ☐ Trial **Scenario E_dip** with guardrails (EMA/VWAP confirm, rise_bars ≥ 2, gate 10–15)  
- ☐ Add **opening RVOL gate** (first 10–15m vs prior day) and **universe hygiene** (exclude ADRs/China, low‑float junk) across all scenarios  
- ☐ Confirm risk model (TP 2.0%, SL 2.5–3.0%, daily max‑loss cap)  
- ☐ Compare August vs September to check regime sensitivity

---

## When We’re Ready
- Implement a **router** with precedence (example: E → D → B), one position per symbol.  
- Emit merged CSV: `out/YYYYMMDD/ROUTER/merged_YYYY-MM-DD.csv` and a summary TXT.  
- Keep per‑scenario outputs for auditability.

---

## Notes
- Hybridization historically improved **stability** and **profit** once scenarios were tuned.  
- We’ll document router design and commands in a separate guide when activated.
