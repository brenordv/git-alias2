import json
from unittest.mock import patch

import pytest

from core.exceptions import ProviderAuthError, RepoCreationError
from core.providers.github import (
    GitHubProvider,
    _extract_token_scopes_from_output,
    _extract_username_from_output,
)


class TestExtractUsername:
    def test_extract_with_as_format(self):
        output = "Logged in to github.com as myuser (oauth_token)"
        assert _extract_username_from_output(output) == "myuser"

    def test_extract_with_account_format(self):
        output = "Logged in to github.com account myuser (oauth_token)"
        assert _extract_username_from_output(output) == "myuser"

    def test_extract_with_unknown_format(self):
        output = "some unexpected output"
        assert _extract_username_from_output(output) == "unknown"


class TestExtractTokenScopes:
    def test_extract_scopes(self):
        output = "Token scopes: repo, read:org, workflow"
        assert _extract_token_scopes_from_output(output) == "repo, read:org, workflow"

    def test_extract_scopes_missing(self):
        output = "no scopes here"
        assert _extract_token_scopes_from_output(output) == "unknown"


class TestGitHubProviderCheckAuth:
    @patch("core.providers.github.run_cli")
    def test_logged_in_as_format(self, mock_run):
        mock_run.return_value = _make_result(
            stderr="Logged in to github.com as testuser (oauth_token)\nToken scopes: repo"
        )
        provider = GitHubProvider()
        is_auth, msg = provider.check_auth()
        assert is_auth is True
        assert "testuser" in msg

    @patch("core.providers.github.run_cli")
    def test_logged_in_account_format(self, mock_run):
        mock_run.return_value = _make_result(
            stderr="Logged in to github.com account testuser (oauth_token)\nToken scopes: repo"
        )
        provider = GitHubProvider()
        is_auth, msg = provider.check_auth()
        assert is_auth is True
        assert "testuser" in msg

    @patch("core.providers.github.run_cli")
    def test_not_logged_in(self, mock_run):
        mock_run.return_value = _make_result(
            stderr="You are not logged into any GitHub hosts."
        )
        provider = GitHubProvider()
        is_auth, msg = provider.check_auth()
        assert is_auth is False


class TestGitHubProviderGetRemoteUrl:
    @patch("core.providers.github.run_cli")
    def test_valid_json(self, mock_run):
        mock_run.return_value = _make_result(
            stdout=json.dumps({"url": "https://github.com/user/repo"})
        )
        provider = GitHubProvider()
        url = provider.get_remote_url("repo")
        assert url == "https://github.com/user/repo.git"

    @patch("core.providers.github.run_cli")
    def test_url_already_has_git_suffix(self, mock_run):
        mock_run.return_value = _make_result(
            stdout=json.dumps({"url": "https://github.com/user/repo.git"})
        )
        provider = GitHubProvider()
        url = provider.get_remote_url("repo")
        assert url == "https://github.com/user/repo.git"

    @patch("core.providers.github.run_cli")
    def test_invalid_json(self, mock_run):
        mock_run.return_value = _make_result(stdout="not json")
        provider = GitHubProvider()
        with pytest.raises(RepoCreationError):
            provider.get_remote_url("repo")

    @patch("core.providers.github.run_cli")
    def test_missing_url_field(self, mock_run):
        mock_run.return_value = _make_result(stdout=json.dumps({"name": "repo"}))
        provider = GitHubProvider()
        with pytest.raises(RepoCreationError):
            provider.get_remote_url("repo")


class TestGitHubProviderCreateRepo:
    @patch("core.providers.github.run_cli")
    def test_success(self, mock_run):
        mock_run.return_value = _make_result(
            stdout="https://github.com/user/my-repo\n"
        )
        provider = GitHubProvider()
        url = provider.create_repo("my-repo")
        assert url == "https://github.com/user/my-repo.git"

    @patch("core.providers.github.run_cli")
    def test_failure(self, mock_run):
        mock_run.return_value = _make_result(stderr="error: repo already exists")
        provider = GitHubProvider()
        with pytest.raises(RepoCreationError):
            provider.create_repo("my-repo")


def _make_result(stdout="", stderr="", returncode=0):
    """Helper to create a mock CompletedProcess."""
    from subprocess import CompletedProcess
    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)
