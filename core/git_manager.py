from pathlib import Path

from git import Repo

from core.decorators import stop_watch
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
