import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.command_wrappers import create_command, fix_create_command
from core.exceptions import GitAliasError, RepoCreationError


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


class TestFixCreateCommand:
    @patch("core.command_wrappers.is_git_repo", return_value=False)
    @patch("core.command_wrappers.config_repo")
    @patch("core.command_wrappers.get_provider")
    @patch("core.command_wrappers.preflight_check")
    def test_skips_create_when_repo_already_exists_on_provider(
        self, mock_preflight, mock_get_provider, mock_config, mock_is_git
    ):
        """When a repo already exists on a provider (e.g. from a partial create),
        fix-create should use get_remote_url instead of calling create_repo."""
        github_provider = MagicMock()
        github_provider.display_name = "GitHub"
        github_provider.get_remote_url.return_value = (
            "https://github.com/user/repo.git"
        )

        azure_provider = MagicMock()
        azure_provider.display_name = "Azure DevOps"
        azure_provider.get_remote_url.side_effect = RepoCreationError("not found")
        azure_provider.create_repo.return_value = (
            "https://dev.azure.com/org/repo/_git/repo"
        )

        def side_effect(name):
            return {"github": github_provider, "azure": azure_provider}[name]

        mock_get_provider.side_effect = side_effect

        with patch("os.getcwd", return_value="/tmp/repo"):
            fix_create_command(["github", "azure"])

        # GitHub: get_remote_url succeeded, create_repo should NOT be called
        github_provider.get_remote_url.assert_called_once_with("repo")
        github_provider.create_repo.assert_not_called()

        # Azure: get_remote_url failed, create_repo SHOULD be called
        azure_provider.get_remote_url.assert_called_once_with("repo")
        azure_provider.create_repo.assert_called_once_with("repo")

        # Both URLs should be passed to config_repo
        call_args = mock_config.call_args
        urls = call_args[0][1]
        assert "https://github.com/user/repo.git" in urls
        assert "https://dev.azure.com/org/repo/_git/repo" in urls

    @patch("core.command_wrappers.is_git_repo", return_value=False)
    @patch("core.command_wrappers.config_repo")
    @patch("core.command_wrappers.get_provider")
    @patch("core.command_wrappers.preflight_check")
    def test_creates_all_when_none_exist(
        self, mock_preflight, mock_get_provider, mock_config, mock_is_git
    ):
        """When no repos exist on any provider, fix-create should create all."""
        github_provider = MagicMock()
        github_provider.display_name = "GitHub"
        github_provider.get_remote_url.side_effect = RepoCreationError("not found")
        github_provider.create_repo.return_value = (
            "https://github.com/user/repo.git"
        )

        mock_get_provider.return_value = github_provider

        with patch("os.getcwd", return_value="/tmp/repo"):
            fix_create_command(["github"])

        github_provider.get_remote_url.assert_called_once()
        github_provider.create_repo.assert_called_once_with("repo")

    @patch("core.command_wrappers.is_git_repo", return_value=False)
    @patch("core.command_wrappers.config_repo")
    @patch("core.command_wrappers.get_provider")
    @patch("core.command_wrappers.preflight_check")
    def test_uses_existing_urls_when_all_repos_already_exist(
        self, mock_preflight, mock_get_provider, mock_config, mock_is_git
    ):
        """When all repos already exist on providers, fix-create should
        use their URLs without calling create_repo."""
        github_provider = MagicMock()
        github_provider.display_name = "GitHub"
        github_provider.get_remote_url.return_value = (
            "https://github.com/user/repo.git"
        )

        azure_provider = MagicMock()
        azure_provider.display_name = "Azure DevOps"
        azure_provider.get_remote_url.return_value = (
            "https://dev.azure.com/org/repo/_git/repo"
        )

        def side_effect(name):
            return {"github": github_provider, "azure": azure_provider}[name]

        mock_get_provider.side_effect = side_effect

        with patch("os.getcwd", return_value="/tmp/repo"):
            fix_create_command(["github", "azure"])

        github_provider.create_repo.assert_not_called()
        azure_provider.create_repo.assert_not_called()

        call_args = mock_config.call_args
        urls = call_args[0][1]
        assert len(urls) == 2
