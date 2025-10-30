# Scenarios for Humans — A Quick Guide (Midas_V2)

This is a plain‑English overview of **Scenarios A–E** so anyone can understand what each one tries to do and how they differ.

---

## Glossary (super short)
- **TP / SL** — take‑profit / stop‑loss (e.g., TP=+2.0%, SL=−2.5%).
- **EMA** — a moving average that gives more weight to recent price (tracks trend closely).
- **VWAP** — volume‑weighted average price (a “fair value” reference line).
- **MACD** — a momentum indicator (is the push actually gaining?).
- **Gate minutes** — how long we wait after the opening bell before a scenario is allowed to trade.

---

## Scenario A — “Fast breakout scalper”
**Idea:** Jump early on strong momentum, grab a small profit quickly.  
**Behavior:** Confirms **on** (EMA, VWAP, MACD), **gate = 0** (no wait), **TP/SL ≈ 1.2% / 2.7%**.  
**Good when:** the opener is very clean/strong. More sensitive to noise.

## Scenario B — “Baseline, patient & confirm‑heavy”
**Idea:** Bread‑and‑butter setup; wait a bit, require strong confirms, aim for a modest win.  
**Behavior:** Confirms **on** (EMA, VWAP, MACD), **gate = 10 min**, **TP/SL ≈ 2.0% / 2.5%**, needs some pre‑market volume (~30k).  
**Status:** Our current baseline.

## Scenario C — “Looser control / experiment”
**Idea:** Lighter confirmation sandbox (often for comparison, not production).  
**Behavior:** **EMA on**, **VWAP off**, **MACD off**, **gate = 0**, **TP/SL ≈ 1.2% / 2.7%**.  
**Trade‑off:** More signals, usually lower quality.

## Scenario D — “Baseline’s earlier twin”
**Idea:** Like B, but allowed to start earlier to catch earlier pushes.  
**Behavior:** Confirms **on** (EMA, VWAP, MACD), **gate = 5 min**, **TP/SL ≈ 2.0% / 2.5%**, pre‑market volume similar to B (~30k).  
**Use when:** B feels late; D adds a few earlier entries.

## Scenario E — “Dip‑reclaim (buy the bounce back)”
**Idea:** Don’t chase the first move—wait for a **pullback**, then a **reclaim** (price loses a key level, then **proves** it can take it back).  
**Behavior:** **Dip‑reclaim ON**, confirms **on** (EMA, VWAP, MACD), **gate = 15 min**, **rise_bars = 3**, higher pre‑market volume (~50k).  
**Use when:** you want patience and proof before entries.

---

## How to pick between them (simple rules)
- Start with **B** as the default.  
- Try **D** if you want earlier entries (gate 5 vs 10).  
- Use **E** when you prefer “wait for the reclaim” behavior.  
- **A** and **C** are more aggressive / experimental (A is fast scalper; C is looser).

---

## Today’s working recipe
- Universe: **gap ≥ 10%**, price **$1–$20**.  
- Catalyst mode: **A‑priority + B‑fill**, **Top‑N = 3** (news fallback enabled).  
- One trade per symbol (re‑entry optional in a later version).
