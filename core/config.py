import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".git-alias2.json"


def _read_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def get_disabled_providers() -> list[str]:
    return _read_config().get("disabled_providers", [])


def is_provider_disabled(name: str) -> bool:
    return name in get_disabled_providers()


def disable_provider(name: str) -> None:
    config = _read_config()
    disabled = config.get("disabled_providers", [])
    if name not in disabled:
        disabled.append(name)
    config["disabled_providers"] = disabled
    _write_config(config)


def enable_provider(name: str) -> None:
    config = _read_config()
    disabled = config.get("disabled_providers", [])
    if name in disabled:
        disabled.remove(name)
    config["disabled_providers"] = disabled
    _write_config(config)


def filter_disabled(provider_names: list[str]) -> tuple[list[str], list[str]]:
    """Split provider names into (active, disabled) lists."""
    disabled = get_disabled_providers()
    active = [p for p in provider_names if p not in disabled]
    skipped = [p for p in provider_names if p in disabled]
    return active, skipped
