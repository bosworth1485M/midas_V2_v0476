# Goal: Read-only HTTP helper for Phase 2a.
# Serve GET /current on 127.0.0.1:5001 returning params from config/scenarios.json.
# No writes in this version. Read-only only.
#
# Requirements:
# - Framework: Flask with CORS for http://localhost:5173 and http://127.0.0.1:5173
# - Endpoint: GET /current?scenario=B (default "B")
# - Read config/scenarios.json and return only fields: top, price_min, price_max
# - Response shape:
#   {"scenario":"B","params":{"top":3,"price_min":1.0,"price_max":20.0}}
# - If file/scenario missing: return small JSON error or empty params object
# - No writes, no POST in this version
#
# Constants:
#   SCENARIOS_PATH = Path("config/scenarios.json")
#   DEFAULT_SCENARIO = "B"
#   ALLOWED_FIELDS = ("top","price_min","price_max")
#
# CLI: python tools/backend/param_helper.py --port 5001
# Keep logs minimal; do not include stack traces in responses.