import re
import shutil
import subprocess

from core.exceptions import ProviderCommandError

_ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def run_cli(
    command: list[str],
    strip_ansi: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a CLI command without shell=True.

    Resolves the command via shutil.which() to handle .cmd/.bat on Windows.
    """
    resolved = shutil.which(command[0])
    if resolved is None:
        raise ProviderCommandError(f"Command not found: {command[0]}")

    cmd = [resolved] + command[1:]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if strip_ansi:
        result = subprocess.CompletedProcess(
            args=result.args,
            returncode=result.returncode,
            stdout=_ANSI_PATTERN.sub("", result.stdout).strip(),
            stderr=_ANSI_PATTERN.sub("", result.stderr).strip(),
        )

    if check and result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        raise ProviderCommandError(
            f"Command failed (exit code {result.returncode}): {' '.join(command)}\n{output}"
        )

    return result


def ensure_git_suffix(url: str) -> str:
    """Ensure a URL ends with .git."""
    clean = url.rstrip("/")
    if not clean.lower().endswith(".git"):
        return clean + ".git"
    return clean
