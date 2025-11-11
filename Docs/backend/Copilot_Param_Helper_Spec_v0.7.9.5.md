# Copilot Implementation Spec — Param Helper (Phase 2a Read-Only)
**Version:** v0.7.9.5
**Purpose:** Serve current parameter values from `config/scenarios.json` to the UI via `GET /current`. **No writes** in this version.

## 0) Constraints & Scope
- **Read-only**: do not modify any files.
- **Port**: `127.0.0.1:5001`
- **File of truth**: `config/scenarios.json`
- **Fields in scope**: `top`, `price_min`, `price_max`
- **Active scenario**: default `"B"`, but allow `?scenario=<ID>` (e.g., `A|B|C|D|E`)

## 1) File & Folder Layout
- Create: `tools/backend/param_helper.py`  ← (single entrypoint)
- Create: `tools/backend/requirements.txt` with:
  - `Flask==3.*`
  - `flask-cors==4.*`  *(to avoid CORS issues from the Vite dev server on 5173)*

## 2) Server Behavior
- Framework: **Flask**.
- CORS: enable for `http://localhost:5173` and `http://127.0.0.1:5173`.
- Config constants (top of file):
  - `SCENARIOS_PATH = Path("config/scenarios.json")`
  - `DEFAULT_SCENARIO = "B"`
  - `ALLOWED_FIELDS = ("top", "price_min", "price_max")`

## 3) Endpoint: `GET /current`
**Query params:**
- `scenario` (optional, default `"B"`)

**Behavior:**
1. Validate `scenario` is a simple alphanumeric/underscore string (A–Z, 0–9, `_`, `-`) to avoid path injection in future.
2. Read `config/scenarios.json` (UTF-8).
3. Extract `params` for the requested scenario. (Assume structure like `{ "B": { "params": { ... } } }` or `{ "scenarios": { "B": { "params": {...} } } }` — support both if practical.)
4. Build a filtered dict with only **ALLOWED_FIELDS** present.
5. Return JSON with shape:
   ```json
   {
     "scenario": "B",
     "params": {
       "top": 3,
       "price_min": 1.0,
       "price_max": 20.0
     }
   }
   ```
6. If file not found / invalid / scenario missing: return 404 JSON:
   ```json
   { "error": "not_found", "message": "Could not load parameters for scenario B." }
   ```
   …and a safe empty `params` object if you prefer HTTP 200 for UI friendliness (either is acceptable; the UI already shows a friendly inline message when fetch fails).

**Headers:**
- `Content-Type: application/json; charset=utf-8`
- CORS headers enabled via `flask_cors.CORS(app, ...)`

## 4) Error Handling & Logging
- Log: startup line with port; each request path + scenario; and any file/JSON errors with concise messages.
- Never print stack traces to the response body.
- Keep responses small and deterministic.

## 5) CLI & Run
- Create a small `if __name__ == "__main__":` block that accepts `--port` (default 5001) and starts Flask with `debug=False`.
- Example run:
  ```bash
  cd <project root>
  python -m venv .venv
  .\.venv\Scripts\activate
  pip install -r tools\backend\requirements.txt
  python tools\backend\param_helper.py --port 5001
  ```

## 6) Manual Test (without UI)
- With server running, test in a new terminal:
  ```bash
  curl "http://127.0.0.1:5001/current?scenario=B"
  ```
- Expected HTTP 200 with:
  ```json
  { "scenario": "B", "params": { "top": <int or null>, "price_min": <number or null>, "price_max": <number or null> } }
  ```

## 7) UI Integration (already implemented)
- The page calls `GET http://127.0.0.1:5001/current` with a 5s timeout.
- On success, it fills **Current** and pre-fills **Proposed**.
- On failure, it shows an inline warning.

## 8) Acceptance Criteria (Phase 2a)
- Helper starts on `127.0.0.1:5001` without errors.
- `GET /current` returns JSON in the **exact** contract shape.
- UI **Load Current** fills values; **Preview** validates and mirrors to **Preview After**; **Apply** remains disabled.
- No file writes occur; no new fields beyond the allow-list are exposed.

## 9) Notes for Phase 2b (future)
- Add `POST /patch?dry_run=1` and `POST /patch?apply=1`.
- Validate allowed fields; **atomic write** to `scenarios.json` with **timestamped backup** (e.g., `scenarios.2025-11-11T13-07-22.bak.json`).
- Return updated `current` on success; show backup filename.
