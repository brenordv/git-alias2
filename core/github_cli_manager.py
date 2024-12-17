# -*- coding: utf-8 -*-
import json
import subprocess
from typing import List

from core.decorators import stop_watch
from core.utils import get_logger

_tag = "[Github]"


def _run_gb_cmd(command: List[str]) -> str:
    # use popen to run the command and capture the output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    # Decode the output and error from bytes to string
    output = output.decode()
    error = error.decode()

    # gb is weird. sometimes it returns the output in the error variable
    return output if output != "" and output is not None else error


def _extract_username_from_output(output: str) -> str:
    try:
        return output.split("github.com as")[1].strip().split(" ")[0].strip()
    except IndexError:
        return output.split("github.com account")[1].strip().split(" ")[0].strip()


def _extract_token_scopes_from_output(output: str) -> str:
    return output.split("scopes:")[1].strip()


@stop_watch(f"{_tag} Checking session")
def _is_logged_in() -> bool:
    logger = get_logger()
    output = _run_gb_cmd(["gh", "auth", "status"])
    l_output = output.lower()

    is_logged = any([msg in l_output for msg in ["logged in to github.com account", "logged in to github.com as"]])
    if not is_logged:
        logger.warning(f"{_tag} Not logged in.")
        return is_logged

    username = _extract_username_from_output(output)
    token_scopes = _extract_token_scopes_from_output(output)
    logger.info(f"{_tag} Logged in as {username} with token scopes '{token_scopes}'")
    return is_logged


@stop_watch(f"{_tag} Logging in")
def _login() -> bool:
    logger = get_logger()
    logger.info(f"{_tag} Due to the way GitHub CLI works, you need to login using another terminal window. Run the "
                f"command below and when logged in, press [Enter] to continue.")
    print("===========================================")
    print("gh auth login -p https -h GitHub.com -w")
    print("===========================================")

    input("After logging in, press [Enter] to continue...")

    if _is_logged_in():
        return True

    raise Exception(f"{_tag} Login failed. Please check your GitHub CLI configuration.")


def _ensure_is_logged_in() -> None:
    if _is_logged_in():
        return
    _login()


@stop_watch(f"{_tag} Fetching repository remote url")
def _get_remote_url(repo_name: str) -> str:
    output = _run_gb_cmd(["gh", "repo", "view", repo_name, "--json", "url"])
    try:
        json_output = json.loads(output)
        repo_url = json_output.get("url")

        if repo_url is None:
            raise Exception(f"{_tag} Could not get remote url. Error: {output}")

        if not repo_url.lower().endswith(".git"):
            repo_url += ".git"

        return repo_url
    except json.JSONDecodeError:
        raise Exception(f"{_tag} Could not get remote url. Error: {output}")
    pass


@stop_watch(f"{_tag} Creating repository")
def _create_github_repo(repo_name: str) -> str:
    logger = get_logger()

    output = _run_gb_cmd(["gh", "repo", "create", repo_name, "--private"])

    if not output.lower().startswith("https"):
        raise Exception(f"{_tag} Repository creation failed. Error: {output}")

    remote_url = output.replace("\n", "").replace("\r", "").strip()
    remote_url += ".git"
    logger.info(f"{_tag} Repository created: {remote_url}")
    return remote_url


def create_github_repo(repo_name):
    _ensure_is_logged_in()
    return _create_github_repo(repo_name)
