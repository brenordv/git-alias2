import json
import shutil

from core.decorators import stop_watch
from core.exceptions import ProviderAuthError, ProviderCommandError, RepoCreationError
from core.providers.base import Provider
from core.subprocess_utils import ensure_git_suffix, run_cli
from core.utils import get_logger

_tag = "[GitLab]"


class GitLabProvider(Provider):
    @property
    def cli_name(self) -> str:
        return "glab"

    @property
    def display_name(self) -> str:
        return "GitLab"

    @property
    def url_pattern(self) -> str:
        return r"gitlab\.com"

    def check_cli(self) -> bool:
        return shutil.which("glab") is not None

    def check_auth(self) -> tuple[bool, str]:
        try:
            result = run_cli(["glab", "auth", "status"], check=False)
        except ProviderCommandError:
            return False, "GitLab CLI not available"

        output = result.stdout or result.stderr
        l_output = output.lower()

        if "logged in" in l_output:
            return True, "Logged in to GitLab"
        return False, "Not logged in to GitLab"

    @stop_watch(f"{_tag} Logging in")
    def login(self) -> None:
        logger = get_logger()
        logger.info(
            f"{_tag} Please login using the GitLab CLI. Run the command below "
            f"in another terminal and press [Enter] when done."
        )
        print("===========================================")
        print("glab auth login")
        print("===========================================")

        input("After logging in, press [Enter] to continue...")

        is_auth, msg = self.check_auth()
        if not is_auth:
            raise ProviderAuthError(f"{_tag} Login failed. {msg}")

    def ensure_logged_in(self) -> None:
        is_auth, msg = self.check_auth()
        if is_auth:
            logger = get_logger()
            logger.info(f"{_tag} {msg}")
            return
        self.login()

    @stop_watch(f"{_tag} Fetching repository remote url")
    def get_remote_url(self, name: str) -> str:
        result = run_cli(
            ["glab", "repo", "view", name, "--output", "json"], check=False
        )
        output = result.stdout or result.stderr
        try:
            json_output = json.loads(output)
            repo_url = json_output.get("http_url_to_repo") or json_output.get(
                "web_url"
            )
            if repo_url is None:
                raise RepoCreationError(
                    f"{_tag} Could not get remote url. Output: {output}"
                )
            return ensure_git_suffix(repo_url)
        except json.JSONDecodeError:
            raise RepoCreationError(
                f"{_tag} Could not get remote url. Output: {output}"
            )

    @stop_watch(f"{_tag} Creating repository")
    def create_repo(self, name: str) -> str:
        logger = get_logger()
        result = run_cli(
            ["glab", "repo", "create", name, "--private", "--defaultBranch", "master"],
            check=False,
        )
        output = (result.stdout or result.stderr).strip()

        if result.returncode != 0:
            raise RepoCreationError(
                f"{_tag} Repository creation failed. Output: {output}"
            )

        # Try to extract URL from output
        for line in output.splitlines():
            line = line.strip()
            if line.lower().startswith("https://"):
                remote_url = ensure_git_suffix(line)
                logger.info(f"{_tag} Repository created: {remote_url}")
                return remote_url

        # If no URL in output, fetch it
        remote_url = self.get_remote_url(name)
        logger.info(f"{_tag} Repository created: {remote_url}")
        return remote_url
