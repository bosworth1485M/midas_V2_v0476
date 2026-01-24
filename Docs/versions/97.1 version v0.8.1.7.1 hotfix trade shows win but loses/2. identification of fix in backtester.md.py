Yes — the fix for v0.8.1.7.1 will live almost entirely in backtester.py, and after reviewing the file you uploaded, we can now be very precise about where and why.

I’ll keep this clear and grounded in what your code is actually doing.

Short answer (direct)

Yes. This is a backtester.py fix.
No strategy files, no scenario JSON, no indicators.

This is execution / accounting correctness, and all of that logic lives here.

Why backtester.py is the correct (and only) place

From the code you shared 

backtester

, all four of these responsibilities are handled inside run_backtest():

Entry price assignment

entry = bar.c


TP / SL calculation

tp, sl = strat.targets(entry)


TP / SL evaluation

if pos_bar.h >= tp:  # TP
elif pos_bar.l <= sl:  # SL


PnL computation and outcome labeling

pnl = (tp - entry) * qty
trades.append((sym, "TP", pnl))


There is no other file where:

outcome is decided,

pnl is calculated,

or the CSV result is written.

So if TP can be negative, the bug must be here.

The exact bug (now visible in your code)

Here is the key contradiction in your current logic:

TP is triggered by high touching TP
if pos_bar.h >= tp:

But PnL is calculated using fixed TP price
pnl = (tp - entry) * qty


That assumes:

tp > entry always

tp was computed from the same entry price

But we already observed cases where:

tp < entry (ICCT)

duplicate timestamps exist

pos_bar ≠ bar (you log [POS_MGMT_MISMATCH])

So the system can:

detect a TP touch on one bar,

but compute pnl using a mismatched tp value,

resulting in TP with negative PnL.

That is exactly what your Apr-07 log proves 

runlog_2025-04-07_B

.

What v0.8.1.7.1 must fix (conceptually)

This version must enforce one invariant inside backtester.py:

Outcome labels must agree with realized economics.

Concretely:

A trade labeled TP must have pnl ≥ 0

A trade labeled SL must have pnl ≤ 0

How that is enforced (without changing strategy) will be done here, not elsewhere.

Where the change will be made (exact region)

The fix belongs inside the “manage open position” block, right here:

# manage open position
if position is not None:
    pos_bar = pos_bar_by_ts.get(bar.ts, bar)

    if pos_bar.h >= tp:
        ...
    elif pos_bar.l <= sl:
        ...


That is the only place where:

TP/SL is decided,

PnL is computed,

outcome is labeled,

and trades are appended.

This is exactly why v0.8.1.7.1 can remain:

single-file,

surgical,

low risk.

What will NOT change

Just to be explicit:

❌ SimpleBreakoutStrategy

❌ strat.targets()

❌ scenario JSON

❌ sizing logic

❌ TWCS logic

❌ indicators

Those stay untouched.

Why this sequencing is correct

Once this fix is in place:

Win% becomes trustworthy again

PnL aligns with outcomes

A/B testing becomes valid

Only after that does it make sense to add:

v0.8.1.8.0 confirm-bar execution safety guard

One-sentence conclusion

Yes — v0.8.1.7.1 is a backtester.py execution-correctness fix, and the exact bug lives in the TP/SL evaluation and PnL labeling logic inside the open-position management block.

If you want, next I can:

draft the locked Copilot spec for v0.8.1.7.1 with exact non-goals, or

propose two minimal correction patterns and explain why one is safer given your logs.

Just tell me which.