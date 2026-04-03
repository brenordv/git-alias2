from core.providers.azure import AzureDevOpsProvider
from core.providers.base import Provider
from core.providers.github import GitHubProvider
from core.providers.gitlab import GitLabProvider

PROVIDERS: dict[str, type[Provider]] = {
    "github": GitHubProvider,
    "azure": AzureDevOpsProvider,
    "gitlab": GitLabProvider,
}

DEFAULT_PROVIDERS = ["github", "azure", "gitlab"]


def get_provider(name: str) -> Provider:
    cls = PROVIDERS.get(name)
    if cls is None:
        available = ", ".join(PROVIDERS)
        raise ValueError(f"Unknown provider: {name}. Available: {available}")
    return cls()
