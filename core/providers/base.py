from abc import ABC, abstractmethod


class Provider(ABC):
    @property
    @abstractmethod
    def cli_name(self) -> str:
        """Name of the CLI tool (e.g., 'gh', 'az', 'glab')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def url_pattern(self) -> str:
        """Regex pattern that matches remote URLs for this provider."""

    @abstractmethod
    def check_cli(self) -> bool:
        """Check if the CLI tool is available on PATH."""

    @abstractmethod
    def check_auth(self) -> tuple[bool, str]:
        """Check authentication status. Returns (is_authenticated, message)."""

    @abstractmethod
    def login(self) -> None:
        """Perform interactive login."""

    @abstractmethod
    def ensure_logged_in(self) -> None:
        """Ensure authenticated, prompting login if needed."""

    @abstractmethod
    def create_repo(self, name: str) -> str:
        """Create a remote repository and return the remote URL."""

    @abstractmethod
    def get_remote_url(self, name: str) -> str:
        """Get the remote URL for an existing repository."""
