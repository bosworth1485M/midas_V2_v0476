Yes — this is exactly the contrast we needed, and it tells us something very important.

I’ll break this down cleanly and then give a concrete recommendation.

1️⃣ What you’ve just proven (very important)

By restoring v0.8.1.7.1 from the memory stick and re-running 2025-04-01 → 2025-04-10, you have produced a clean A baseline that is:

internally consistent (thanks to TP/SL rebase),

economically sensible,

and not collapsed.

From the end of your log:

=== TOTALS ===
[B] trades=7, wins=4, losses=3, winrate=57.14%, totalPnL=+2.82


This is the true A reference for April 1–10 under Scenario B in v0.8.1.7.1. 

B_runlog_20250401_20250410_v0.8…

That matters because:

The same date range under v0.8.1.8.0 collapsed to near-zero trades.

Therefore, the difference is not market regime, not data, and not randomness.

The difference is entirely explained by the new Confirm-Bar guard.

This is the cleanest A/B isolation you could have hoped for.

2️⃣ Why the results are “very different” (root cause)
In v0.8.1.7.1 (baseline)

Trades are allowed even if:

the confirmation bar dips below the stop intrabar,

but that dip is only visible after duplicate-timestamp merging.

Examples you already identified:

JNVR (2025-04-07)

MESA (2025-04-07)

NWTG (2025-04-07)

These trades:

are technically executable in the backtester,

but are structurally invalid in real execution (you’re stopped before you’re in).

That’s why TWCS flagged them.

In v0.8.1.8.0 (current implementation)

The guard now checks:

confirm_bar = pos_bar_by_ts.get(bar.ts, bar)


This means:

if any duplicate bar at that timestamp has a low below the stop,

the trade is blocked.

This is correct from a “safety” standpoint, but it is very strict.

Result:

Many April trades are blocked,

April becomes almost trade-less.

So the difference you’re seeing is not a bug — it’s the logical consequence of a stricter execution rule.

3️⃣ Why this does NOT mean v0.8.1.8.0 is “wrong”

This is crucial:

v0.8.1.7.1 allows trades that TWCS proved are invalid

v0.8.1.8.0 correctly blocks those trades

So the question is not:

“Why did v0.8.1.8.0 lose trades?”

The real question is:

“Is v0.8.1.8.0 blocking only structurally invalid trades, or also blocking trades that could have been valid?”

That’s a policy decision, not a correctness decision.

4️⃣ What this tells us about the Confirm-Bar Guard

You’ve now learned:

The guard works exactly as specified

It matches TWCS evidence

It has a large behavioral impact

That impact comes mainly from:

duplicate timestamps,

wick-correct merging,

taking the minimum low across duplicates.

This is why the April cluster collapsed.

5️⃣ What I recommend (very clear next step)
❌ Do NOT tag v0.8.1.8.0 yet

Not because it’s broken — but because we need to decide which interpretation of “confirm bar” we want.

You now have two valid options:

✅ Option A — “Strict Safety” (current code)

Definition:

If any intrabar wick at confirm time breaches stop → reject.

Pros

Maximum realism

Never enter a trade already stopped

TWCS-aligned

Cons

Very conservative

Trade frequency drops sharply

Sensitive to data duplication artifacts

This is acceptable only if August/September still trade.

⚖️ Option B — “Executable Confirm Bar”

Definition:

Use the actual bar used to confirm entry (not merged lows) for the guard.

That means:

guard uses bar (the entry decision bar),

TP/SL evaluation remains wick-correct later.

Pros

Blocks obvious instant stops (JNVR-type)

Preserves most baseline trade count

Less sensitive to duplicate data artifacts

Cons

Slightly less strict than full wick-merge safety

6️⃣ What to do next (recommended sequence)

Keep v0.8.1.8.0 untagged

Run the August cluster (e.g. 2025-08-05 → 2025-08-09) with the current guard

If August also collapses:

revise guard to Option B,

re-run April + August,

then tag.

This fits your permanent workflow:

time-diverse validation,

TWCS-driven,

reversible guard logic.

7️⃣ Bottom line (plain English)

v0.8.1.7.1 shows what can be traded.
v0.8.1.8.0 shows what should not be traded.
The remaining work is deciding how strict “should not” needs to be.

You did exactly the right thing by restoring the baseline — this comparison is rock-solid.