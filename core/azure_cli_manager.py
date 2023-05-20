# -*- coding: utf-8 -*-
import json
import subprocess
from typing import List

from core.decorators import stop_watch
from core.utils import get_logger, run_external_command

_tag = "[Azure]"


def _run_az_cmd(command: List[str]) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.replace("[0m", "").replace("", "").strip()
        return output
    except FileNotFoundError:
        raise Exception("Azure CLI (az) command not found.")


@stop_watch(f"{_tag} Checking session")
def _is_logged_in() -> bool:
    logger = get_logger()
    output = _run_az_cmd(["az", "account", "show"])
    try:
        json_output = json.loads(output)

        subscription_type = "default" if json_output.get("isDefault", False) else "alternative"
        subscription_name = json_output.get("name", "unknown")
        subscription_state = json_output.get("state", "unknown")
        user_name = json_output.get("user", {}).get("name", "unknown").split("@")[0]
        logger.info(
            f"{_tag} Logged in as {user_name} with {subscription_type} subscription '{subscription_name}' ({subscription_state})")

        return True
    except json.JSONDecodeError:
        logger.warning(f"{_tag} Not logged in.")
        return False


@stop_watch(f"{_tag} Logging in")
def _login() -> bool:
    output = _run_az_cmd(["az", "login"])
    try:
        json.loads(output)
        return _is_logged_in()

    except json.JSONDecodeError:
        raise Exception(f"{_tag} Login failed. Please check your Azure CLI configuration. Error: {output}")


def _ensure_is_logged_in() -> None:
    if _is_logged_in():
        return
    _login()


@stop_watch(f"{_tag} Fetching repository remote url")
def _get_remote_url(repo_name: str) -> str:
    output = _run_az_cmd(["az", "repos", "show", "--project", repo_name, "--repository", repo_name])
    try:
        json_output = json.loads(output)
        repo_url = json_output.get("remoteUrl")

        if repo_url is None:
            raise Exception(f"{_tag} Could not get remote url. Error: {output}")

        return repo_url
    except json.JSONDecodeError:
        raise Exception(f"{_tag} Could not get remote url. Error: {output}")


@stop_watch(f"{_tag} Creating project + repository")
def _create_azure_project(project_name: str) -> str:
    logger = get_logger()

    output = _run_az_cmd(
        ["az", "devops", "project", "create", "--name", project_name, "--visibility", "private", "--source-control",
         "git"])
    try:
        json_output = json.loads(output)
        project_id = json_output.get("id")
        project_name = json_output.get("name")
        project_state = json_output.get("state")

        if project_state != "wellFormed":
            raise Exception(f"{_tag} Project creation failed. State: {project_state}")

        logger.info(f"{_tag} Project created: {project_name} ({project_id})")
        remote_url = _get_remote_url(project_name)
        logger.info(f"{_tag} Repository created: {remote_url}")

        return remote_url

    except json.JSONDecodeError:
        raise Exception(f"{_tag} Project creation failed. Error: {output}")


def create_azure_repo(repo_name):
    _ensure_is_logged_in()
    return _create_azure_project(repo_name)
