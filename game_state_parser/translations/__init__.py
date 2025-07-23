import json
import os
from typing import Dict

translations: Dict[str, str] = json.load(open(os.path.join(os.path.dirname(__file__), "en.json")))


def t(key: str | None, path=None) -> str:
    full = f"{key}.{path}" if path else (key or "unknown")
    return translations.get(full, full)
