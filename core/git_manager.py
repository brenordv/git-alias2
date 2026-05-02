from pathlib import Path

from git import GitCommandError, Repo

from core.decorators import stop_watch
from core.exceptions import GitOperationError
from core.utils import get_logger

_tag = "[Git]"


@stop_watch(f"{_tag} Repository creation.")
def _init_repo(folder_path: Path) -> Repo:
    logger = get_logger()
    logger.info(f"{_tag} Initializing repository in {folder_path}")
    return Repo.init(folder_path)


@stop_watch(f"{_tag} Repository remote setup.")
def _repo_remote_setup(repo: Repo, remote_repo_urls: list[str]) -> None:
    logger = get_logger()
    remote = repo.create_remote("origin", remote_repo_urls[0])

    for remote_repo_url in remote_repo_urls[1:]:
        logger.info(f"{_tag} Adding remote repo: {remote_repo_url}")
        remote.add_url(remote_repo_url)


def config_repo(folder_path: Path, remote_repo_urls: list[str]) -> None:
    repo = _init_repo(folder_path)
    _repo_remote_setup(repo, remote_repo_urls)


@stop_watch(f"{_tag} Checkout branch.")
def checkout_branch(repo: Repo, branch: str = "master") -> None:
    logger = get_logger()
    logger.info(f"{_tag} Checking out branch '{branch}'")
    try:
        repo.heads[branch].checkout()
    except IndexError as e:
        raise GitOperationError(f"Branch '{branch}' not found") from e


@stop_watch(f"{_tag} Pull latest changes.")
def pull(repo: Repo) -> None:
    logger = get_logger()
    logger.info(f"{_tag} Pulling latest changes from origin")
    try:
        repo.remotes.origin.pull()
    except GitCommandError as e:
        raise GitOperationError(f"Pull failed: {e}") from e


@stop_watch(f"{_tag} Create tag.")
def create_tag(repo: Repo, tag_name: str, message: str) -> None:
    logger = get_logger()
    logger.info(f"{_tag} Creating tag '{tag_name}'")
    try:
        repo.create_tag(tag_name, message=message)
    except GitCommandError as e:
        raise GitOperationError(f"Failed to create tag '{tag_name}': {e}") from e


@stop_watch(f"{_tag} Push tag.")
def push_tag(repo: Repo, tag_name: str) -> None:
    logger = get_logger()
    logger.info(f"{_tag} Pushing tag '{tag_name}' to origin")
    try:
        result = repo.remotes.origin.push(tag_name)
        if result and result[0].flags & result[0].ERROR:
            raise GitOperationError(
                f"Push rejected for tag '{tag_name}': {result[0].summary}"
            )
    except GitCommandError as e:
        raise GitOperationError(f"Failed to push tag '{tag_name}': {e}") from e
