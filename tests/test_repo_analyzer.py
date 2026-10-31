from pathlib import Path

from git import Repo

from core.repo_analyzer import detect_repo_name, get_existing_remotes, get_missing_providers, is_git_repo


def _repo_with_origin(path: Path, urls: list[str]) -> Repo:
    repo = Repo.init(path)
    remote = repo.create_remote("origin", urls[0])
    for url in urls[1:]:
        remote.add_url(url)
    return repo


class TestGetExistingRemotes:
    def test_urls_are_grouped_by_provider(self, tmp_path: Path) -> None:
        _repo_with_origin(
            tmp_path,
            [
                "https://github.com/me/repo.git",
                "https://me@dev.azure.com/me/repo/_git/repo",
                "https://gitlab.com/me/repo.git",
            ],
        )

        remotes = get_existing_remotes(tmp_path)

        assert remotes == {
            "github": ["https://github.com/me/repo.git"],
            "azure": ["https://me@dev.azure.com/me/repo/_git/repo"],
            "gitlab": ["https://gitlab.com/me/repo.git"],
        }

    def test_unknown_hosts_are_ignored(self, tmp_path: Path) -> None:
        _repo_with_origin(tmp_path, ["https://example.com/me/repo.git"])

        assert get_existing_remotes(tmp_path) == {}


class TestDetectRepoName:
    def test_strips_git_suffix(self) -> None:
        assert detect_repo_name({"github": ["https://github.com/me/my-repo.git"]}) == "my-repo"

    def test_azure_url_without_suffix(self) -> None:
        assert detect_repo_name({"azure": ["https://dev.azure.com/me/proj/_git/my-repo/"]}) == "my-repo"

    def test_percent_escapes_are_decoded(self) -> None:
        assert detect_repo_name({"azure": ["https://dev.azure.com/me/my%20repo/_git/my%20repo"]}) == "my repo"

    def test_no_remotes_returns_empty_string(self) -> None:
        assert detect_repo_name({}) == ""


class TestGetMissingProviders:
    def test_returns_desired_providers_without_remotes_in_order(self) -> None:
        remotes = {"github": ["https://github.com/me/repo.git"]}

        assert get_missing_providers(remotes, ["github", "azure", "gitlab"]) == ["azure", "gitlab"]


class TestIsGitRepo:
    def test_true_for_initialized_repo(self, tmp_path: Path) -> None:
        Repo.init(tmp_path)

        assert is_git_repo(tmp_path) is True

    def test_false_for_plain_folder(self, tmp_path: Path) -> None:
        assert is_git_repo(tmp_path) is False
