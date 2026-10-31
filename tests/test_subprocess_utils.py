from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from core.exceptions import ProviderCommandError
from core.subprocess_utils import ensure_git_suffix, run_cli


class TestRunCli:
    @patch("core.subprocess_utils.shutil.which", return_value=None)
    def test_missing_command_raises(self, _mock_which: MagicMock) -> None:
        with pytest.raises(ProviderCommandError, match="Command not found: gh"):
            run_cli(["gh", "auth", "status"])

    @patch("core.subprocess_utils.subprocess.run")
    @patch("core.subprocess_utils.shutil.which", return_value="resolved-gh")
    def test_runs_resolved_command_without_shell(self, _mock_which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")

        result = run_cli(["gh", "auth", "status"])

        mock_run.assert_called_once_with(["resolved-gh", "auth", "status"], capture_output=True, text=True)
        assert result.stdout == "ok"

    @patch("core.subprocess_utils.subprocess.run")
    @patch("core.subprocess_utils.shutil.which", return_value="resolved-gh")
    def test_failure_raises_when_checked(self, _mock_which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")

        with pytest.raises(ProviderCommandError, match="exit code 1"):
            run_cli(["gh", "repo", "create", "x"])

    @patch("core.subprocess_utils.subprocess.run")
    @patch("core.subprocess_utils.shutil.which", return_value="resolved-gh")
    def test_failure_is_returned_when_unchecked(self, _mock_which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")

        result = run_cli(["gh", "repo", "create", "x"], check=False)

        assert result.returncode == 1

    @patch("core.subprocess_utils.subprocess.run")
    @patch("core.subprocess_utils.shutil.which", return_value="resolved-az")
    def test_strip_ansi_removes_color_codes(self, _mock_which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout="\x1b[32m{}\x1b[0m\n", stderr="")

        result = run_cli(["az", "devops", "project", "list"], strip_ansi=True)

        assert result.stdout == "{}"


class TestEnsureGitSuffix:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://github.com/me/repo", "https://github.com/me/repo.git"),
            ("https://github.com/me/repo/", "https://github.com/me/repo.git"),
            ("https://github.com/me/repo.git", "https://github.com/me/repo.git"),
            ("https://github.com/me/repo.GIT", "https://github.com/me/repo.GIT"),
        ],
    )
    def test_adds_suffix_only_when_missing(self, url: str, expected: str) -> None:
        assert ensure_git_suffix(url) == expected
