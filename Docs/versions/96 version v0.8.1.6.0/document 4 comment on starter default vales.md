In the Copilot spec I proposed starter default values for the new knobs:

post_entry_expansion_minutes = 2

post_entry_expansion_min_bps = 10

post_entry_expansion_gate = false (OFF by default)

Those numbers are not proven yet — they’re just an initial “first test” setting so you can A/B the feature.

Two ways to handle defaults (both valid)

Keep the defaults as-is (recommended)
Use 2 minutes / 10 bps as the first pass. If it blocks too much or too little, we adjust later in a new version or a controlled A/B run.

Change the defaults now
If you already have a strong prior (from TWCS) that “2 minutes is too short” or “10 bps is too weak,” we can set different starting values before Copilot codes anything.

My recommendation

Keep them as written:

minutes = 2

min_bps = 10

gate = false by default

Because v0.8.1.7.0 is about testing the hypothesis, not tuning. We’ll learn from the sanity days first, then adjust only if needed.

If you want to change them anyway, tell me what you prefer for:

minutes (2 vs 3)

min_bps (10 vs 15 vs 20)

…and I’ll update the Copilot spec accordingly.