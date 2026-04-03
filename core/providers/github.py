import json
import shutil

from core.decorators import stop_watch
from core.exceptions import ProviderAuthError, ProviderCommandError, RepoCreationError
from core.providers.base import Provider
from core.subprocess_utils import ensure_git_suffix, run_cli
from core.utils import get_logger

_tag = "[GitHub]"


class GitHubProvider(Provider):
    @property
    def cli_name(self) -> str:
        return "gh"

    @property
    def display_name(self) -> str:
        return "GitHub"

    @property
    def url_pattern(self) -> str:
        return r"github\.com"

    def check_cli(self) -> bool:
        return shutil.which("gh") is not None

    def check_auth(self) -> tuple[bool, str]:
        try:
            result = run_cli(["gh", "auth", "status"], check=False)
        except ProviderCommandError:
            return False, "GitHub CLI not available"

        output = result.stdout or result.stderr
        l_output = output.lower()

        is_logged = any(
            msg in l_output
            for msg in ["logged in to github.com account", "logged in to github.com as"]
        )

        if is_logged:
            username = _extract_username_from_output(output)
            scopes = _extract_token_scopes_from_output(output)
            return True, f"Logged in as {username} (scopes: {scopes})"

        return False, "Not logged in to GitHub"

    @stop_watch(f"{_tag} Logging in")
    def login(self) -> None:
        logger = get_logger()
        logger.info(
            f"{_tag} Due to the way GitHub CLI works, you need to login using another "
            f"terminal window. Run the command below and when logged in, press [Enter] "
            f"to continue."
        )
        print("===========================================")
        print("gh auth login -p https -h GitHub.com -w")
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
        result = run_cli(["gh", "repo", "view", name, "--json", "url"], check=False)
        output = result.stdout or result.stderr
        try:
            json_output = json.loads(output)
            repo_url = json_output.get("url")
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
        result = run_cli(["gh", "repo", "create", name, "--private"], check=False)
        output = (result.stdout or result.stderr).strip()

        if not output.lower().startswith("https"):
            raise RepoCreationError(
                f"{_tag} Repository creation failed. Output: {output}"
            )

        remote_url = ensure_git_suffix(
            output.replace("\n", "").replace("\r", "").strip()
        )
        logger.info(f"{_tag} Repository created: {remote_url}")
        return remote_url


def _extract_username_from_output(output: str) -> str:
    try:
        return output.split("github.com as")[1].strip().split(" ")[0].strip()
    except IndexError:
        try:
            return output.split("github.com account")[1].strip().split(" ")[0].strip()
        except IndexError:
            return "unknown"


def _extract_token_scopes_from_output(output: str) -> str:
    try:
        return output.split("scopes:")[1].strip()
    except IndexError:
        return "unknown"
