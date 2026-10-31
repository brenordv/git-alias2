from unittest.mock import MagicMock, patch

import pytest

from core.diagnostics import doctor, preflight_check, suggest_fix
from core.exceptions import ProviderCommandError


class TestSuggestFix:
    @pytest.mark.parametrize(
        ("error_text", "expected"),
        [
            ("Command not found: gh", "Install GitHub CLI: https://cli.github.com/"),
            ("authentication required", "Run: gh auth login -p https -h GitHub.com -w"),
            ("permission denied", "Create a new token at: https://github.com/settings/tokens"),
            ("something unrelated", ""),
        ],
    )
    def test_matches_error_text_to_provider_fix(self, error_text: str, expected: str) -> None:
        assert suggest_fix(Exception(error_text), "github") == expected

    def test_no_provider_returns_empty(self) -> None:
        assert suggest_fix(Exception("Command not found: gh")) == ""


class TestPreflightCheck:
    @patch("core.diagnostics.get_provider")
    def test_missing_cli_raises_with_install_hint(self, mock_get_provider: MagicMock) -> None:
        provider = MagicMock(display_name="GitHub", cli_name="gh")
        provider.check_cli.return_value = False
        mock_get_provider.return_value = provider

        with pytest.raises(ProviderCommandError, match="Install GitHub CLI"):
            preflight_check(["github"])

    @patch("core.diagnostics.get_provider")
    def test_unauthenticated_provider_only_warns(self, mock_get_provider: MagicMock) -> None:
        provider = MagicMock(display_name="GitHub", cli_name="gh")
        provider.check_cli.return_value = True
        provider.check_auth.return_value = (False, "Not logged in to GitHub")
        mock_get_provider.return_value = provider

        preflight_check(["github"])

        provider.check_auth.assert_called_once()


class TestDoctor:
    def test_reports_disabled_missing_and_authenticated_providers(self, capsys: pytest.CaptureFixture[str]) -> None:
        disabled = MagicMock(display_name="GitLab", cli_name="glab")
        missing = MagicMock(display_name="Azure DevOps", cli_name="az")
        missing.check_cli.return_value = False
        authenticated = MagicMock(display_name="GitHub", cli_name="gh")
        authenticated.check_cli.return_value = True
        authenticated.check_auth.return_value = (True, "Logged in as someone")
        providers = {
            "github": MagicMock(return_value=authenticated),
            "azure": MagicMock(return_value=missing),
            "gitlab": MagicMock(return_value=disabled),
        }

        with (
            patch("core.diagnostics.PROVIDERS", providers),
            patch("core.diagnostics.get_disabled_providers", return_value=["gitlab"]),
        ):
            doctor()

        output = capsys.readouterr().out
        assert "GitHub (gh):" in output
        assert "Auth: OK - Logged in as someone" in output
        assert "CLI:  NOT FOUND" in output
        assert "Fix:  Install Azure CLI" in output
        assert "GitLab (glab): [DISABLED]" in output
        disabled.check_cli.assert_not_called()
