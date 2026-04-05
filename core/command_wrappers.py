import os
from pathlib import Path

from core.config import filter_disabled
from core.diagnostics import preflight_check, suggest_fix
from core.exceptions import GitAliasError
from core.git_manager import config_repo
from core.providers.registry import DEFAULT_PROVIDERS, get_provider
from core.repo_analyzer import (
    detect_repo_name,
    get_existing_remotes,
    get_missing_providers,
    is_git_repo,
)
from core.utils import get_logger


def create_command(repo_name: str, provider_names: list[str] | None = None) -> None:
    provider_names = provider_names or list(DEFAULT_PROVIDERS)
    logger = get_logger()

    provider_names, skipped = filter_disabled(provider_names)
    for s in skipped:
        logger.warning(f"Skipping disabled provider: {s} (use 'g enable {s}' to re-enable)")

    if not provider_names:
        logger.error("All requested providers are disabled. Nothing to do.")
        return

    preflight_check(provider_names)

    remote_urls: list[str] = []
    for name in provider_names:
        try:
            provider = get_provider(name)
            provider.ensure_logged_in()
            url = provider.create_repo(repo_name)
            remote_urls.append(url)
        except GitAliasError as e:
            fix = suggest_fix(e, name)
            logger.error(f"Failed to create repo on {name}: {e}")
            if fix:
                logger.info(f"Suggestion: {fix}")
            if remote_urls:
                logger.warning(
                    f"Partial success: repos created on {len(remote_urls)} provider(s). "
                    f"Use 'g fix-create' to add missing providers."
                )
            raise

    config_repo(Path(os.getcwd()), remote_urls)


def fix_create_command(provider_names: list[str] | None = None) -> None:
    provider_names = provider_names or list(DEFAULT_PROVIDERS)
    logger = get_logger()

    provider_names, skipped = filter_disabled(provider_names)
    for s in skipped:
        logger.warning(f"Skipping disabled provider: {s} (use 'g enable {s}' to re-enable)")

    if not provider_names:
        logger.error("All requested providers are disabled. Nothing to do.")
        return

    cwd = Path(os.getcwd())

    if is_git_repo(cwd):
        remotes = get_existing_remotes(cwd)
        repo_name = detect_repo_name(remotes)
        missing = get_missing_providers(remotes, provider_names)

        if not missing:
            logger.info("All desired providers are already configured.")
            return

        if not repo_name:
            logger.error(
                "Could not detect repository name from existing remotes. "
                "Use 'g create <name>' instead."
            )
            return

        logger.info(f"Detected repo name: {repo_name}")
        logger.info(f"Missing providers: {', '.join(missing)}")
    else:
        logger.info("No git repository found. Treating all providers as missing.")
        missing = provider_names
        repo_name = cwd.name

    preflight_check(missing)

    new_urls: list[str] = []
    for name in missing:
        try:
            provider = get_provider(name)
            provider.ensure_logged_in()

            try:
                url = provider.get_remote_url(repo_name)
                logger.info(
                    f"{provider.display_name} repo already exists: {url}"
                )
            except GitAliasError:
                url = provider.create_repo(repo_name)
                logger.info(f"Created {provider.display_name} repo: {url}")

            new_urls.append(url)
        except GitAliasError as e:
            fix = suggest_fix(e, name)
            logger.error(f"Failed to create repo on {name}: {e}")
            if fix:
                logger.info(f"Suggestion: {fix}")
            raise

    if not is_git_repo(cwd):
        config_repo(cwd, new_urls)
    else:
        from git import Repo

        repo = Repo(cwd)
        if "origin" in [r.name for r in repo.remotes]:
            origin = repo.remote("origin")
            for url in new_urls:
                logger.info(f"Adding push URL: {url}")
                origin.add_url(url)
        else:
            config_repo(cwd, new_urls)


def add_remote_command(
    provider_name: str,
    repo_name: str | None = None,
    set_fetch: bool = False,
) -> None:
    logger = get_logger()
    cwd = Path(os.getcwd())

    if not is_git_repo(cwd):
        logger.error("Not a git repository. Run 'g create <name>' first.")
        return

    if repo_name is None:
        remotes = get_existing_remotes(cwd)
        repo_name = detect_repo_name(remotes)
        if not repo_name:
            logger.error(
                "Could not detect repository name. Use --repo-name to specify it."
            )
            return

    preflight_check([provider_name])

    provider = get_provider(provider_name)
    provider.ensure_logged_in()
    url = provider.create_repo(repo_name)
    logger.info(f"Created {provider.display_name} repo: {url}")

    from git import Repo

    repo = Repo(cwd)

    if set_fetch:
        # Save existing URLs before modifying
        existing_urls: list[str] = []
        if "origin" in [r.name for r in repo.remotes]:
            existing_urls = list(repo.remote("origin").urls)
            repo.delete_remote("origin")

        # Create origin with new URL as fetch target
        remote = repo.create_remote("origin", url)

        # Re-add old URLs as push targets
        for existing_url in existing_urls:
            if existing_url != url:
                remote.add_url(existing_url)

        logger.info(f"Set {provider.display_name} as fetch remote")
    else:
        if "origin" in [r.name for r in repo.remotes]:
            repo.remote("origin").add_url(url)
        else:
            repo.create_remote("origin", url)
        logger.info(f"Added {provider.display_name} as push URL")
