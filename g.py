import argparse
import sys

from core.command_wrappers import add_remote_command, create_command, fix_create_command
from core.config import disable_provider, enable_provider, is_provider_disabled
from core.diagnostics import doctor
from core.exceptions import GitAliasError
from core.providers.registry import DEFAULT_PROVIDERS, PROVIDERS

parser = argparse.ArgumentParser(prog="g", description="Git Alias")
subparsers = parser.add_subparsers(dest="command", help="Available commands")

# create
create_parser = subparsers.add_parser(
    "create",
    help="Creates repositories on configured providers and sets up the local repository.",
)
create_parser.add_argument("repo_name", type=str, help="Name of the repository")
create_parser.add_argument(
    "--providers",
    nargs="+",
    choices=list(PROVIDERS.keys()),
    default=list(DEFAULT_PROVIDERS),
    help=f"Providers to create repos on (default: {' '.join(DEFAULT_PROVIDERS)})",
)

# fix-create
fix_create_parser = subparsers.add_parser(
    "fix-create",
    help="Detects missing providers in an existing repo and creates them.",
)
fix_create_parser.add_argument(
    "--providers",
    nargs="+",
    choices=list(PROVIDERS.keys()),
    default=list(DEFAULT_PROVIDERS),
    help=f"Desired providers (default: {' '.join(DEFAULT_PROVIDERS)})",
)

# add-remote
add_remote_parser = subparsers.add_parser(
    "add-remote",
    help="Add a single provider remote to the current repository.",
)
add_remote_parser.add_argument(
    "provider",
    choices=list(PROVIDERS.keys()),
    help="Provider to add",
)
add_remote_parser.add_argument(
    "--repo-name",
    help="Override auto-detected repository name",
)
add_remote_parser.add_argument(
    "--set-fetch",
    action="store_true",
    help="Make this the primary fetch remote",
)

# disable
disable_parser = subparsers.add_parser(
    "disable",
    help="Disable a provider (skipped in create/fix-create until re-enabled).",
)
disable_parser.add_argument(
    "provider",
    choices=list(PROVIDERS.keys()),
    help="Provider to disable",
)

# enable
enable_parser = subparsers.add_parser(
    "enable",
    help="Re-enable a previously disabled provider.",
)
enable_parser.add_argument(
    "provider",
    choices=list(PROVIDERS.keys()),
    help="Provider to enable",
)

# doctor
subparsers.add_parser("doctor", help="Run diagnostics and report system status.")


def main():
    args = parser.parse_args()

    try:
        if args.command == "create":
            create_command(args.repo_name, args.providers)
        elif args.command == "fix-create":
            fix_create_command(args.providers)
        elif args.command == "add-remote":
            add_remote_command(args.provider, args.repo_name, args.set_fetch)
        elif args.command == "disable":
            if is_provider_disabled(args.provider):
                print(f"{args.provider} is already disabled.")
            else:
                disable_provider(args.provider)
                print(f"Disabled {args.provider}. It will be skipped in create/fix-create.")
                print(f"Use 'g enable {args.provider}' to re-enable.")
        elif args.command == "enable":
            if not is_provider_disabled(args.provider):
                print(f"{args.provider} is already enabled.")
            else:
                enable_provider(args.provider)
                print(f"Enabled {args.provider}.")
                print(f"Use 'g fix-create' to create repos on any missing providers.")
        elif args.command == "doctor":
            doctor()
        else:
            parser.print_help()
    except GitAliasError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
