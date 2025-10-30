# Postmortem — Env/Auth, Prev-Day, Regression (v0.3.9)
- Problem: 401 due to query-string auth / shadowed env; fixed by header auth + sanitized key (override .env).
- Prev day: walk back until resultsCount>0 (skip holidays); logic intact.
- Regression: Aug D baseline reproduced; Sept D (to 09-09) smoke OK.
