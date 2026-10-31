from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the provider config at a per-test file, so no test reads or writes the real ``~/.git-alias2.json``."""
    monkeypatch.setattr("core.config.CONFIG_PATH", tmp_path / "git-alias2.json")
