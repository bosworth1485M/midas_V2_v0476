# Midas Project – Workflow Principles

**Date:** 2025-09-07  
**Version Context:** v0.3.7-cleanup  

---

## 1. Versioning Discipline
- **Tag often, tag early.** Each stable step gets a Git tag (e.g., v0.3.6-prev-trading-day-fix, v0.3.7-cleanup).  
- Versions create *restore points* → you can always roll back if something breaks.  
- Avoid large jumps without checkpoints.

---

## 2. Safe Cleanup
- We archive unused scripts instead of deleting them.  
- `_archive_unused/YYYYMMDD/` keeps old files accessible without cluttering the repo.  
- This preserves history while ensuring the active repo stays clean.

---

## 3. Scenario Modularity
- Scenarios A–E are tested separately first.  
- Each scenario has a role (baseline, strict, dip-reclaim, etc.).  
- **Never hybridize too early** — weaknesses must be visible before combining.

---

## 4. Guardrails First, Profit Later
- Prioritize **win rate stability** with filters: EMA/VWAP confirm, MACD rise bars, RVOL at open, universe hygiene.  
- Profit boosters (multi-trade per symbol, adaptive sizing, 1-second candles) come only after stability.  
- This mirrors Ross Cameron’s real approach: fewer but higher-quality trades.

---

## 5. Documentation as a Safety Net
- Every major step gets an MD + PDF in `Docs/versions/`.  
- This creates a **living history** of decisions, so you never lose context.  
- Easy to revisit “why we did X” months later.

---

## 6. Reversibility & Transparency
- All actions (cleanup, tweaks, router, deletions) are reversible thanks to:  
  - Git commits + tags  
  - Archived files  
  - Backup zips of old projects  
- Transparency means we always know what changed, when, and why.

---

## 7. Future Hybridization
- Only after A–E are tuned individually, we introduce a **router** with precedence (e.g., E → D → B).  
- Hybridization is for *stability across regimes*, not as a quick fix.  
- It will be documented and versioned as its own milestone.

---

## Conclusion
The “cleverness” of the Midas workflow isn’t magic — it’s **discipline, modularity, and documentation**.  
By tagging often, archiving safely, and documenting every step, we protect progress while steadily improving win rate and profitability.  

