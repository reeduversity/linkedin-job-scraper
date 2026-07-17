"""Check that required Python dependencies are installed and print versions.

Exits with code 0 if all found, otherwise 1.
"""
from __future__ import annotations

import importlib
import sys
from importlib import metadata

REQUIREMENTS = {
    "requests": "requests",
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "psycopg": "psycopg",
    "python-dotenv": "dotenv",
    "apscheduler": "apscheduler",
    "pydantic": "pydantic",
    "pydantic-settings": "pydantic_settings",
    "tenacity": "tenacity",
    "rich": "rich",
    "loguru": "loguru",
    "typing-extensions": "typing_extensions",
    "apify-client": "apify_client",
}


def get_version(dist_name: str, module) -> str:
    # Prefer module.__version__, fall back to importlib.metadata
    ver = getattr(module, "__version__", None)
    if ver:
        return str(ver)
    try:
        return metadata.version(dist_name)
    except Exception:
        return "unknown"


def main() -> int:
    missing = []
    for dist, module_name in REQUIREMENTS.items():
        try:
            module = importlib.import_module(module_name)
            version = get_version(dist, module)
            print(f"OK: {dist} (module {module_name}) version: {version}")
        except Exception as exc:  # ImportError or other
            print(f"MISSING: {dist} -> failed to import module '{module_name}': {exc}")
            missing.append(dist)

    if missing:
        print("\nSome packages are missing:", ", ".join(missing))
        return 1

    print("\nAll required packages are installed.")
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
