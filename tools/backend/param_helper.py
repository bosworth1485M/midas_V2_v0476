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
import shutil
from datetime import datetime

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


def _find_scenario(data: Any, scenario: str):
	"""Locate a scenario in the loaded data.
	Returns a tuple (container_type, key_or_index, scenario_obj) where
	container_type is 'dict' or 'list' or None if not found.
	"""
	if isinstance(data, dict):
		if scenario in data:
			return ("dict", scenario, data.get(scenario))
	if isinstance(data, list):
		for idx, item in enumerate(data):
			if isinstance(item, dict) and item.get("id") == scenario:
				return ("list", idx, item)
	return (None, None, None)


def _write_with_backup(data: Any, path: Path) -> Optional[str]:
	"""Write `data` as JSON to `path` atomically, creating a timestamped backup.
	Returns the backup filename (basename) or None if no backup was created.
	"""
	# Ensure parent dir exists
	path.parent.mkdir(parents=True, exist_ok=True)
	# If original file exists, create a timestamped backup
	if path.exists():
		stamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
		backup_name = f"{path.stem}.{stamp}.bak{path.suffix}"
		backup_path = path.with_name(backup_name)
		shutil.copy2(path, backup_path)
		backup_basename = backup_path.name
	else:
		backup_basename = None

	# Atomic write: write to a temp file in same directory then replace
	temp_path = path.with_suffix(path.suffix + ".new")
	with temp_path.open("w", encoding="utf-8") as f:
		json.dump(data, f, indent=2)
	temp_path.replace(path)
	return backup_basename


@app.route("/patch", methods=["POST"])
def patch_scenario():
	"""POST /patch?dry_run=1 or ?apply=1
	Body JSON: {"top": <int>} - only 'top' may be updated in Phase 2b.
	"""
	scenario = request.args.get("scenario", DEFAULT_SCENARIO)
	dry = request.args.get("dry_run") == "1"
	apply_flag = request.args.get("apply") == "1"
	if dry and apply_flag:
		return jsonify({"error": "Specify only one of dry_run=1 or apply=1"}), 400

	body = request.get_json(silent=True)
	if not isinstance(body, dict) or "top" not in body:
		return jsonify({"error": "Missing 'top' in JSON body"}), 400

	# Validate top
	new_top = body.get("top")
	try:
		new_top_int = int(new_top)
		if new_top_int < 1:
			raise ValueError()
	except Exception:
		return jsonify({"error": "Invalid 'top' value; must be integer >= 1"}), 400

	data = _load_scenarios(SCENARIOS_PATH)
	if data is None:
		return jsonify({"error": "scenarios file missing or invalid"}), 400

	container, key, scenario_obj = _find_scenario(data, scenario)
	if not scenario_obj or not isinstance(scenario_obj, dict):
		return jsonify({"error": "scenario not found"}), 400

	params_before = _filter_params(scenario_obj)
	params_after = dict(params_before)
	params_after["top"] = new_top_int
	applied_fields = []
	if params_before.get("top") != new_top_int:
		applied_fields.append("top")

	# Dry run: report the changes, do not write
	if dry:
		return jsonify({
			"scenario": scenario,
			"params_before": params_before,
			"params_after": params_after,
			"applied_fields": applied_fields,
			"dry_run": True,
		}), 200

	# Apply: modify in-memory and write with backup
	if apply_flag:
		# Update the in-memory structure
		if container == "dict":
			data[key]["top"] = new_top_int
		elif container == "list":
			data[key]["top"] = new_top_int
		else:
			return jsonify({"error": "unsupported scenarios.json structure"}), 400

		try:
			backup_file = _write_with_backup(data, SCENARIOS_PATH)
		except Exception as e:
			logger.info("Failed to write scenarios file: %s", e)
			return jsonify({"error": "Failed to write scenarios file"}), 500

		return jsonify({
			"scenario": scenario,
			"params_before": params_before,
			"params_after": params_after,
			"applied_fields": applied_fields,
			"dry_run": False,
			"backup_file": backup_file,
		}), 200

	return jsonify({"error": "Specify either dry_run=1 to simulate or apply=1 to apply"}), 400


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
