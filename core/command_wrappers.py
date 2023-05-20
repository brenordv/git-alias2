# -*- coding: utf-8 -*-
import os
from pathlib import Path

from core.azure_cli_manager import create_azure_repo
from core.git_manager import config_repo
from core.github_cli_manager import create_github_repo


def create_command(repo_name) -> None:
    github_remote_url = create_github_repo(repo_name)
    az_remote_url = create_azure_repo(repo_name)
    remote_urls = [github_remote_url, az_remote_url]

    config_repo(Path(os.getcwd()), remote_urls)
