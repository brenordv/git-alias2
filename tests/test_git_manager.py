import os
import tempfile
from pathlib import Path

from git import Repo

from core.git_manager import config_repo


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
