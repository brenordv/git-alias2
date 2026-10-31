import json
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from core.exceptions import ProviderAuthError, ProviderCommandError, RepoCreationError
from core.providers.gitlab import GitLabProvider


def _make_result(stdout: str = "", stderr: str = "", returncode: int = 0) -> CompletedProcess[str]:
    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class TestGitLabProviderCheckAuth:
    @patch("core.providers.gitlab.run_cli")
    def test_logged_in(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(stderr="gitlab.com\n  ✓ Logged in to gitlab.com as someone")

        is_auth, _ = GitLabProvider().check_auth()

        assert is_auth is True

    @patch("core.providers.gitlab.run_cli")
    def test_not_logged_in_message_is_not_mistaken_for_logged_in(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(stderr="gitlab.com: not logged in")

        is_auth, msg = GitLabProvider().check_auth()

        assert is_auth is False
        assert msg == "Not logged in to GitLab"

    @patch("core.providers.gitlab.run_cli", side_effect=ProviderCommandError("Command not found: glab"))
    def test_cli_missing(self, _mock_run: MagicMock) -> None:
        is_auth, msg = GitLabProvider().check_auth()

        assert is_auth is False
        assert msg == "GitLab CLI not available"


class TestGitLabProviderLogin:
    @patch("builtins.input", return_value="")
    @patch.object(GitLabProvider, "check_auth", return_value=(False, "Not logged in to GitLab"))
    def test_login_raises_when_still_not_authenticated(self, _mock_auth: MagicMock, _mock_input: MagicMock) -> None:
        with pytest.raises(ProviderAuthError, match="Login failed"):
            GitLabProvider().login()

    @patch.object(GitLabProvider, "login")
    @patch.object(GitLabProvider, "check_auth", return_value=(True, "Logged in to GitLab"))
    def test_ensure_logged_in_skips_login_when_authenticated(
        self, _mock_auth: MagicMock, mock_login: MagicMock
    ) -> None:
        GitLabProvider().ensure_logged_in()

        mock_login.assert_not_called()


class TestGitLabProviderGetRemoteUrl:
    @patch("core.providers.gitlab.run_cli")
    def test_prefers_http_url_to_repo(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(
            stdout=json.dumps(
                {"http_url_to_repo": "https://gitlab.com/me/repo.git", "web_url": "https://gitlab.com/me/repo"}
            )
        )

        assert GitLabProvider().get_remote_url("repo") == "https://gitlab.com/me/repo.git"

    @patch("core.providers.gitlab.run_cli")
    def test_falls_back_to_web_url_with_git_suffix(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(stdout=json.dumps({"web_url": "https://gitlab.com/me/repo"}))

        assert GitLabProvider().get_remote_url("repo") == "https://gitlab.com/me/repo.git"

    @patch("core.providers.gitlab.run_cli")
    def test_missing_urls_raise(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(stdout=json.dumps({"id": 1}))

        with pytest.raises(RepoCreationError, match="Could not get remote url"):
            GitLabProvider().get_remote_url("repo")

    @patch("core.providers.gitlab.run_cli")
    def test_invalid_json_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(stderr="404 Not Found")

        with pytest.raises(RepoCreationError, match="Could not get remote url"):
            GitLabProvider().get_remote_url("repo")


class TestGitLabProviderCreateRepo:
    @patch("core.providers.gitlab.run_cli")
    def test_url_from_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(stdout="✓ Created repository\nhttps://gitlab.com/me/repo\n")

        assert GitLabProvider().create_repo("repo") == "https://gitlab.com/me/repo.git"

    @patch.object(GitLabProvider, "get_remote_url", return_value="https://gitlab.com/me/repo.git")
    @patch("core.providers.gitlab.run_cli")
    def test_fetches_url_when_output_has_none(self, mock_run: MagicMock, mock_get_url: MagicMock) -> None:
        mock_run.return_value = _make_result(stdout="✓ Created repository me/repo")

        assert GitLabProvider().create_repo("repo") == "https://gitlab.com/me/repo.git"
        mock_get_url.assert_called_once_with("repo")

    @patch("core.providers.gitlab.run_cli")
    def test_failure_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = _make_result(stderr="name has already been taken", returncode=1)

        with pytest.raises(RepoCreationError, match="already been taken"):
            GitLabProvider().create_repo("repo")
