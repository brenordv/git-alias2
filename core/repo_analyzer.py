import re
from pathlib import Path

from git import InvalidGitRepositoryError, Repo

from core.providers.registry import PROVIDERS


def get_existing_remotes(repo_path: Path) -> dict[str, list[str]]:
    """Read git remotes and categorize URLs by provider."""
    repo = Repo(repo_path)
    result: dict[str, list[str]] = {}

    for remote in repo.remotes:
        for url in remote.urls:
            for name, provider_cls in PROVIDERS.items():
                provider = provider_cls()
                if re.search(provider.url_pattern, url):
                    result.setdefault(name, []).append(url)

    return result


def detect_repo_name(remotes: dict[str, list[str]]) -> str:
    """Extract repo name from existing remote URLs."""
    for urls in remotes.values():
        for url in urls:
            name = url.rstrip("/").split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
    return ""


def get_missing_providers(
    remotes: dict[str, list[str]], desired: list[str]
) -> list[str]:
    """Return provider names that are not yet configured as remotes."""
    return [p for p in desired if p not in remotes]


def is_git_repo(path: Path) -> bool:
    """Check if the given path is inside a git repository."""
    try:
        Repo(path)
        return True
    except InvalidGitRepositoryError:
        return False
