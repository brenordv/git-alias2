import json
import shutil

from core.decorators import stop_watch
from core.exceptions import ProviderAuthError, ProviderCommandError, RepoCreationError
from core.providers.base import Provider
from core.subprocess_utils import run_cli
from core.utils import get_logger

_tag = "[Azure]"


class AzureDevOpsProvider(Provider):
    @property
    def cli_name(self) -> str:
        return "az"

    @property
    def display_name(self) -> str:
        return "Azure DevOps"

    @property
    def url_pattern(self) -> str:
        return r"dev\.azure\.com|visualstudio\.com"

    def check_cli(self) -> bool:
        return shutil.which("az") is not None

    def check_auth(self) -> tuple[bool, str]:
        try:
            result = run_cli(
                ["az", "devops", "project", "list"], strip_ansi=True, check=False
            )
        except ProviderCommandError:
            return False, "Azure CLI not available"

        try:
            json_output = json.loads(result.stdout)
            projects = json_output.get("value", [])
            return True, f"Logged in. Found {len(projects)} project(s)."
        except json.JSONDecodeError:
            return False, "Not logged in to Azure DevOps"

    @stop_watch(f"{_tag} Logging in")
    def login(self) -> None:
        try:
            run_cli(["az", "devops", "login"], check=False)
        except ProviderCommandError as e:
            raise ProviderAuthError(f"{_tag} Login failed: {e}")

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
            ["az", "repos", "show", "--project", name, "--repository", name],
            strip_ansi=True,
            check=False,
        )

        if result.returncode != 0:
            output = result.stderr or result.stdout
            raise RepoCreationError(
                f"{_tag} Could not get remote url. Output: {output}"
            )

        try:
            json_output = json.loads(result.stdout)
            repo_url = json_output.get("remoteUrl")
            if repo_url is None:
                raise RepoCreationError(
                    f"{_tag} Could not get remote url. Output: {result.stdout}"
                )
            return repo_url
        except json.JSONDecodeError:
            raise RepoCreationError(
                f"{_tag} Could not get remote url. Output: {result.stderr or result.stdout}"
            )

    @stop_watch(f"{_tag} Creating project + repository")
    def create_repo(self, name: str) -> str:
        logger = get_logger()
        result = run_cli(
            [
                "az", "devops", "project", "create",
                "--name", name,
                "--visibility", "private",
                "--source-control", "git",
            ],
            strip_ansi=True,
            check=False,
        )

        if result.returncode != 0:
            output = result.stderr or result.stdout
            raise RepoCreationError(
                f"{_tag} Project creation failed. Output: {output}"
            )

        try:
            json_output = json.loads(result.stdout)
            project_id = json_output.get("id")
            project_name = json_output.get("name")
            project_state = json_output.get("state")

            if project_state != "wellFormed":
                raise RepoCreationError(
                    f"{_tag} Project creation failed. State: {project_state}"
                )

            logger.info(f"{_tag} Project created: {project_name} ({project_id})")
            remote_url = self.get_remote_url(project_name)
            logger.info(f"{_tag} Repository created: {remote_url}")
            return remote_url

        except json.JSONDecodeError:
            raise RepoCreationError(
                f"{_tag} Project creation failed. Output: {result.stderr or result.stdout}"
            )
