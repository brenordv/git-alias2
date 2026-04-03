class GitAliasError(Exception):
    """Base exception for git_alias2."""


class ProviderAuthError(GitAliasError):
    """Raised when authentication with a provider fails."""


class ProviderCommandError(GitAliasError):
    """Raised when a provider CLI command fails."""


class RepoCreationError(GitAliasError):
    """Raised when repository creation fails."""
