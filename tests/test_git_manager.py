import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from git import GitCommandError, Repo

from core.exceptions import GitOperationError
from core.git_manager import checkout_branch, config_repo, create_tag, pull, push_tag


class TestConfigRepo:
    def test_initializes_repo_and_sets_remotes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            urls = [
                "https://github.com/user/repo.git",
                "https://dev.azure.com/org/repo/_git/repo",
            ]
            config_repo(Path(tmpdir), urls)

            repo = Repo(tmpdir)
            assert "origin" in [r.name for r in repo.remotes]

            origin = repo.remote("origin")
            origin_urls = list(origin.urls)
            assert origin_urls[0] == "https://github.com/user/repo.git"
            assert "https://dev.azure.com/org/repo/_git/repo" in origin_urls

    def test_single_remote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            urls = ["https://github.com/user/repo.git"]
            config_repo(Path(tmpdir), urls)

            repo = Repo(tmpdir)
            origin = repo.remote("origin")
            origin_urls = list(origin.urls)
            assert len(origin_urls) == 1
            assert origin_urls[0] == "https://github.com/user/repo.git"

    def test_github_url_is_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            urls = [
                "https://github.com/user/repo.git",
                "https://dev.azure.com/org/repo/_git/repo",
                "https://gitlab.com/user/repo.git",
            ]
            config_repo(Path(tmpdir), urls)

            repo = Repo(tmpdir)
            origin = repo.remote("origin")
            origin_urls = list(origin.urls)
            # First URL is the fetch URL
            assert origin_urls[0] == "https://github.com/user/repo.git"
            assert len(origin_urls) == 3


class TestCheckoutBranch:
    def test_missing_branch_raises_git_operation_error(self, tmp_path: Path) -> None:
        repo = Repo.init(tmp_path)

        with pytest.raises(GitOperationError, match="Branch 'master' not found"):
            checkout_branch(repo, "master")

    def test_failed_checkout_raises_git_operation_error(self) -> None:
        repo = MagicMock()
        repo.heads.__getitem__.return_value.checkout.side_effect = GitCommandError(
            "checkout", 1, stderr="local changes"
        )

        with pytest.raises(GitOperationError, match="Checkout of 'master' failed"):
            checkout_branch(repo, "master")


class TestPullTagAndPush:
    def test_failed_pull_raises_git_operation_error(self) -> None:
        repo = MagicMock()
        repo.remotes.origin.pull.side_effect = GitCommandError("pull", 1)

        with pytest.raises(GitOperationError, match="Pull failed"):
            pull(repo)

    def test_failed_tag_raises_git_operation_error(self) -> None:
        repo = MagicMock()
        repo.create_tag.side_effect = GitCommandError("tag", 128, stderr="already exists")

        with pytest.raises(GitOperationError, match="Failed to create tag 'v1.0.0'"):
            create_tag(repo, "v1.0.0", "New version: v1.0.0")

    def test_rejected_push_raises_git_operation_error(self) -> None:
        push_info = MagicMock(flags=1, ERROR=1, summary="rejected")
        repo = MagicMock()
        repo.remotes.origin.push.return_value = [push_info]

        with pytest.raises(GitOperationError, match="Push rejected for tag 'v1.0.0'"):
            push_tag(repo, "v1.0.0")

    def test_successful_push_does_not_raise(self) -> None:
        push_info = MagicMock(flags=0, ERROR=1, summary="ok")
        repo = MagicMock()
        repo.remotes.origin.push.return_value = [push_info]

        push_tag(repo, "v1.0.0")

        repo.remotes.origin.push.assert_called_once_with("v1.0.0")
