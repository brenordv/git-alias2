import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.command_wrappers import create_command
from core.exceptions import RepoCreationError


class TestCreateCommand:
    @patch("core.command_wrappers.config_repo")
    @patch("core.command_wrappers.get_provider")
    @patch("core.command_wrappers.preflight_check")
    def test_creates_repos_in_order(self, mock_preflight, mock_get_provider, mock_config):
        github_provider = MagicMock()
        github_provider.create_repo.return_value = "https://github.com/user/repo.git"
        github_provider.display_name = "GitHub"

        azure_provider = MagicMock()
        azure_provider.create_repo.return_value = "https://dev.azure.com/org/repo/_git/repo"
        azure_provider.display_name = "Azure DevOps"

        def side_effect(name):
            return {"github": github_provider, "azure": azure_provider}[name]

        mock_get_provider.side_effect = side_effect

        create_command("my-repo", ["github", "azure"])

        # Verify providers were called in order
        github_provider.ensure_logged_in.assert_called_once()
        github_provider.create_repo.assert_called_once_with("my-repo")
        azure_provider.ensure_logged_in.assert_called_once()
        azure_provider.create_repo.assert_called_once_with("my-repo")

        # Verify config_repo was called with GitHub URL first
        call_args = mock_config.call_args
        urls = call_args[0][1]
        assert urls[0] == "https://github.com/user/repo.git"
        assert urls[1] == "https://dev.azure.com/org/repo/_git/repo"

    @patch("core.command_wrappers.config_repo")
    @patch("core.command_wrappers.get_provider")
    @patch("core.command_wrappers.preflight_check")
    def test_partial_failure_reports_guidance(self, mock_preflight, mock_get_provider, mock_config):
        github_provider = MagicMock()
        github_provider.create_repo.return_value = "https://github.com/user/repo.git"
        github_provider.display_name = "GitHub"

        azure_provider = MagicMock()
        azure_provider.create_repo.side_effect = RepoCreationError("Azure failed")
        azure_provider.display_name = "Azure DevOps"

        def side_effect(name):
            return {"github": github_provider, "azure": azure_provider}[name]

        mock_get_provider.side_effect = side_effect

        with pytest.raises(RepoCreationError, match="Azure failed"):
            create_command("my-repo", ["github", "azure"])

        # config_repo should NOT have been called due to failure
        mock_config.assert_not_called()

    @patch("core.command_wrappers.config_repo")
    @patch("core.command_wrappers.get_provider")
    @patch("core.command_wrappers.preflight_check")
    def test_single_provider(self, mock_preflight, mock_get_provider, mock_config):
        provider = MagicMock()
        provider.create_repo.return_value = "https://github.com/user/repo.git"
        provider.display_name = "GitHub"
        mock_get_provider.return_value = provider

        create_command("my-repo", ["github"])

        call_args = mock_config.call_args
        urls = call_args[0][1]
        assert len(urls) == 1
        assert urls[0] == "https://github.com/user/repo.git"
