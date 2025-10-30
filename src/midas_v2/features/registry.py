from __future__ import annotations
from pathlib import Path
import json

class FeatureRegistry:
    _cfg = {}
    _root: Path | None = None

    @classmethod
    def load(cls, root: Path) -> None:
        cls._root = root; cls._cfg.clear()
        feat_dir = root / "config" / "features"
        if not feat_dir.exists(): return
        for p in feat_dir.glob("*.json"):
            try: cls._cfg[p.stem] = json.loads(p.read_text(encoding="utf-8"))
            except Exception: pass

    @classmethod
    def is_enabled(cls, feature: str, scenario_id: str) -> bool:
        f = cls._cfg.get(feature, {})
        if "enable_for" in f: return scenario_id in set(map(str, f["enable_for"]))
        return bool(f.get("enabled", False))

    @classmethod
    def get(cls, feature: str, key: str, default=None):
        return cls._cfg.get(feature, {}).get(key, default)