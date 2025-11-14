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
from pathlib import Path
import json
import argparse
import logging
from typing import Dict, Any, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

# Constants
SCENARIOS_PATH = Path("config/scenarios.json")
DEFAULT_SCENARIO = "B"
ALLOWED_FIELDS = ("top", "price_min", "price_max")

app = Flask(__name__)
# Only allow the frontend origins used in Phase 2a
CORS(app, resources={r"/*": {"origins": [
	"http://localhost:5173",
	"http://127.0.0.1:5173",
]}})

# Minimal logger
logger = logging.getLogger("param_helper")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _load_scenarios(path: Path) -> Optional[Dict[str, Any]]:
	"""Load scenarios JSON from disk. Returns mapping or None if not found/invalid."""
	try:
		with path.open("r", encoding="utf-8") as f:
			return json.load(f)
	except FileNotFoundError:
		logger.info("scenarios file not found: %s", path)
		return None
	except json.JSONDecodeError:
		logger.info("scenarios file invalid JSON: %s", path)
		return None


def _filter_params(scenario_obj: Dict[str, Any]) -> Dict[str, Any]:
	"""Return a dict containing only ALLOWED_FIELDS if present."""
	params: Dict[str, Any] = {}
	for key in ALLOWED_FIELDS:
		if key in scenario_obj:
			params[key] = scenario_obj[key]
	return params


@app.route("/current", methods=["GET"])
def get_current():
	"""GET /current?scenario=<id> -> {"scenario": id, "params": {...}}"""
	scenario = request.args.get("scenario", DEFAULT_SCENARIO)

	data = _load_scenarios(SCENARIOS_PATH)
	if not data or not isinstance(data, dict):
		# Return empty params when file missing/invalid
		return jsonify({"scenario": scenario, "params": {}}), 200

	# scenarios.json may be a dict mapping ids to objects, or a list.
	scenario_obj = None
	if scenario in data:
		scenario_obj = data.get(scenario)
	else:
		# If the file stores a list of scenarios with id fields, try to find it
		if isinstance(data, list):
			for item in data:
				if isinstance(item, dict) and item.get("id") == scenario:
					scenario_obj = item
					break

	if not scenario_obj or not isinstance(scenario_obj, dict):
		return jsonify({"scenario": scenario, "params": {}}), 200

	params = _filter_params(scenario_obj)
	return jsonify({"scenario": scenario, "params": params}), 200


def _parse_args() -> argparse.Namespace:
	p = argparse.ArgumentParser(description="Read-only param helper for Phase 2a")
	p.add_argument("--port", type=int, default=5001, help="Port to listen on (default 5001)")
	p.add_argument("--host", default="127.0.0.1", help="Host to bind to (default 127.0.0.1)")
	return p.parse_args()


if __name__ == "__main__":
	args = _parse_args()
	logger.info("Starting param_helper on %s:%s", args.host, args.port)
	# Run in production mode: disable Flask reloader to avoid double logging
	app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
