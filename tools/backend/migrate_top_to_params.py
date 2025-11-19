"""Migrate root-level 'top' keys into nested 'params' dict for scenarios.json.

This script follows these rules:
- Reads `config/scenarios.json` (expected to be a mapping of scenario_id -> scenario_obj).
- For each scenario object that is a dict and contains a top-level 'top' key,
  moves that value into `scenario_obj['params']['top']`, creating `params` if needed.
- Before writing any changes it writes a backup named `scenarios.top_migration.bak.json`
  next to the original file containing the original content.
- Writes back the updated file with `json.dump(..., indent=2, sort_keys=True)`.
- Prints a short summary at the end listing how many scenarios were migrated and their keys.

The script is safe to run multiple times: if no scenario has a root-level 'top', no changes are made.
"""

from pathlib import Path
import json
import shutil
from typing import Dict, Any, List


SCENARIOS_PATH = Path("config") / "scenarios.json"
BACKUP_NAME = "scenarios.top_migration.bak.json"


def load_json(path: Path) -> Any:
	with path.open("r", encoding="utf-8") as f:
		return json.load(f)


def write_json(path: Path, data: Any) -> None:
	# Write pretty-printed JSON with sorted keys
	with path.open("w", encoding="utf-8") as f:
		json.dump(data, f, indent=2, sort_keys=True)


def backup_original(path: Path, backup_name: str) -> Path:
	backup_path = path.with_name(backup_name)
	shutil.copy2(path, backup_path)
	return backup_path


def migrate_top_to_params(data: Dict[str, Any]) -> List[str]:
	"""Migrate root-level 'top' into nested params for each scenario.

	Returns a list of scenario keys that were modified.
	"""
	modified: List[str] = []
	# Expect data to be a mapping of scenario_id -> scenario_obj
	if not isinstance(data, dict):
		return modified

	for key, value in data.items():
		if not isinstance(value, dict):
			continue
		if "top" in value:
			top_value = value.pop("top")
			params = value.get("params")
			if params is None or not isinstance(params, dict):
				params = {}
				value["params"] = params
			# Only set if not already present or to override with the root-level value
			params["top"] = top_value
			modified.append(key)

	return modified


def main() -> None:
	if not SCENARIOS_PATH.exists():
		print(f"scenarios file not found: {SCENARIOS_PATH}")
		return

	original = load_json(SCENARIOS_PATH)

	# Work on a deep copy (json load returned a fresh object anyway)
	data = original

	modified_keys = migrate_top_to_params(data)

	if not modified_keys:
		print("Migrated 0 scenarios")
		return

	# Backup original
	backup_path = backup_original(SCENARIOS_PATH, BACKUP_NAME)

	# Write updated data
	write_json(SCENARIOS_PATH, data)

	print(f"Migrated {len(modified_keys)} scenarios: {', '.join(modified_keys)}")
	print(f"Backup written to: {backup_path}")


if __name__ == "__main__":
	main()