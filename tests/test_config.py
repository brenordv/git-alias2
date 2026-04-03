import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from core.config import (
    disable_provider,
    enable_provider,
    filter_disabled,
    get_disabled_providers,
    is_provider_disabled,
)


def _with_temp_config(func):
    """Run a test with a temporary config file."""
    def wrapper(*args, **kwargs):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp = Path(f.name)
            f.write("{}")
        try:
            with patch("core.config.CONFIG_PATH", tmp):
                return func(*args, **kwargs)
        finally:
            tmp.unlink(missing_ok=True)
    return wrapper


class TestDisableProvider:
    @_with_temp_config
    def test_disable_adds_to_list(self):
        disable_provider("gitlab")
        assert "gitlab" in get_disabled_providers()

    @_with_temp_config
    def test_disable_twice_is_idempotent(self):
        disable_provider("gitlab")
        disable_provider("gitlab")
        assert get_disabled_providers().count("gitlab") == 1

    @_with_temp_config
    def test_disable_multiple_providers(self):
        disable_provider("gitlab")
        disable_provider("azure")
        disabled = get_disabled_providers()
        assert "gitlab" in disabled
        assert "azure" in disabled


class TestEnableProvider:
    @_with_temp_config
    def test_enable_removes_from_list(self):
        disable_provider("gitlab")
        enable_provider("gitlab")
        assert "gitlab" not in get_disabled_providers()

    @_with_temp_config
    def test_enable_already_enabled_is_noop(self):
        enable_provider("gitlab")
        assert "gitlab" not in get_disabled_providers()


class TestIsProviderDisabled:
    @_with_temp_config
    def test_disabled_returns_true(self):
        disable_provider("azure")
        assert is_provider_disabled("azure") is True

    @_with_temp_config
    def test_enabled_returns_false(self):
        assert is_provider_disabled("github") is False


class TestFilterDisabled:
    @_with_temp_config
    def test_filters_disabled(self):
        disable_provider("azure")
        active, skipped = filter_disabled(["github", "azure", "gitlab"])
        assert active == ["github", "gitlab"]
        assert skipped == ["azure"]

    @_with_temp_config
    def test_none_disabled(self):
        active, skipped = filter_disabled(["github", "azure"])
        assert active == ["github", "azure"]
        assert skipped == []

    @_with_temp_config
    def test_all_disabled(self):
        disable_provider("github")
        disable_provider("azure")
        active, skipped = filter_disabled(["github", "azure"])
        assert active == []
        assert skipped == ["github", "azure"]
