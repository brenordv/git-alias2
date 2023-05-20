# -*- coding: utf-8 -*-
import argparse

from core.command_wrappers import create_command


# Initialize the parser
parser = argparse.ArgumentParser(prog="g", description="Git Alias")

# Define subparsers
subparsers = parser.add_subparsers(dest="command", help='Available commands')

# Define "create" command
create_parser = subparsers.add_parser("create", help="Creates a repository in GitHub and Azure DevOps, then sets up the"
                                                     " local repository.")

# Define flags for the "create" command
create_parser.add_argument('repo_name', type=str, help="Name of the repository that will be created")


def main():
    args = parser.parse_args()
    if args.command == 'create':
        create_command(args.repo_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
