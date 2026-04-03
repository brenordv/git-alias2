import shutil

from core.config import get_disabled_providers
from core.exceptions import ProviderCommandError
from core.providers.registry import PROVIDERS, get_provider
from core.utils import get_logger

_FIX_SUGGESTIONS: dict[str, dict[str, str]] = {
    "gh": {
        "not_found": "Install GitHub CLI: https://cli.github.com/",
        "auth_failed": "Run: gh auth login -p https -h GitHub.com -w",
        "permission": "Create a new token at: https://github.com/settings/tokens",
    },
    "az": {
        "not_found": "Install Azure CLI: https://aka.ms/install-azure-cli",
        "auth_failed": "Run: az devops login",
        "permission": (
            "Create a PAT at your Azure DevOps org: "
            "User Settings > Personal Access Tokens"
        ),
    },
    "glab": {
        "not_found": "Install GitLab CLI: https://gitlab.com/gitlab-org/cli",
        "auth_failed": "Run: glab auth login",
        "permission": (
            "Create a token at: "
            "https://gitlab.com/-/user_settings/personal_access_tokens"
        ),
    },
}


def check_cli_available(cli_name: str) -> bool:
    return shutil.which(cli_name) is not None


def check_cli_auth(provider_name: str) -> tuple[bool, str]:
    provider = get_provider(provider_name)
    return provider.check_auth()


def suggest_fix(error: Exception, provider_name: str = "") -> str:
    error_str = str(error).lower()

    if provider_name:
        provider = get_provider(provider_name)
        fixes = _FIX_SUGGESTIONS.get(provider.cli_name, {})

        if "not found" in error_str or "command not found" in error_str:
            return fixes.get("not_found", "")
        if "auth" in error_str or "login" in error_str or "token" in error_str:
            return fixes.get("auth_failed", "")
        if "permission" in error_str or "forbidden" in error_str:
            return fixes.get("permission", "")

    return ""


def preflight_check(provider_names: list[str]) -> None:
    logger = get_logger()
    errors: list[str] = []

    for name in provider_names:
        provider = get_provider(name)

        if not provider.check_cli():
            fix = _FIX_SUGGESTIONS.get(provider.cli_name, {}).get("not_found", "")
            msg = f"{provider.display_name}: CLI tool '{provider.cli_name}' not found."
            if fix:
                msg += f" {fix}"
            errors.append(msg)
            continue

        is_auth, status_msg = provider.check_auth()
        if is_auth:
            logger.info(f"{provider.display_name}: {status_msg}")
        else:
            logger.warning(f"{provider.display_name}: {status_msg}")

    if errors:
        raise ProviderCommandError(
            "Preflight check failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )


def doctor() -> None:
    disabled = get_disabled_providers()

    print("Git Alias Doctor")
    print("=" * 40)

    for name, provider_cls in PROVIDERS.items():
        provider = provider_cls()
        is_disabled = name in disabled
        status_suffix = " [DISABLED]" if is_disabled else ""
        print(f"\n{provider.display_name} ({provider.cli_name}):{status_suffix}")

        if is_disabled:
            print(f"  Status: DISABLED (use 'g enable {name}' to re-enable)")
            continue

        if not provider.check_cli():
            fix = _FIX_SUGGESTIONS.get(provider.cli_name, {}).get("not_found", "")
            print(f"  CLI:  NOT FOUND")
            if fix:
                print(f"  Fix:  {fix}")
            continue

        print(f"  CLI:  OK ({shutil.which(provider.cli_name)})")

        is_auth, msg = provider.check_auth()
        if is_auth:
            print(f"  Auth: OK - {msg}")
        else:
            fix = _FIX_SUGGESTIONS.get(provider.cli_name, {}).get("auth_failed", "")
            print(f"  Auth: FAILED - {msg}")
            if fix:
                print(f"  Fix:  {fix}")

    print()
