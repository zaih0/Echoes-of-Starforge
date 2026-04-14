import json
import sys
from typing import Any, Dict


SAVE_FILE = "save_data.json"
LOCAL_STORAGE_KEY = "echoes_of_starforge_save"


def is_web() -> bool:
    return sys.platform == "emscripten"


def _load_from_local_storage() -> Dict[str, Any]:
    try:
        from platform import window  # type: ignore

        raw = window.localStorage.getItem(LOCAL_STORAGE_KEY)
        if not raw:
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def _save_to_local_storage(data: Dict[str, Any]) -> None:
    try:
        from platform import window  # type: ignore

        window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
    except Exception:
        pass


def load_save_data() -> Dict[str, Any]:
    if is_web():
        return _load_from_local_storage()

    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def write_save_data(data: Dict[str, Any]) -> None:
    if is_web():
        _save_to_local_storage(data)
        return

    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def has_run_save() -> bool:
    data = load_save_data()
    return "run" in data
