# Git Alias 2
This project is a collection of git "aliases" that I use frequently.
It automates multi-provider git repository creation (GitHub, Azure DevOps, GitLab).

## Note about this project
Why use the CLI applications (gh, az, glab) instead of the APIs? Mainly to avoid leaving tokens around with too many
permissions. Since I already have the CLI applications installed, I can use them to create the repos without having to
create new tokens and having to worry about leaking them (or having to renew every x days).

That being said: You need to have the CLI applications installed and configured for the providers you want to use:
- **GitHub**: `gh` — https://cli.github.com/
- **Azure DevOps**: `az` — https://aka.ms/install-azure-cli
- **GitLab**: `glab` — https://gitlab.com/gitlab-org/cli

## Installation

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup
1. Clone this repository
2. Install dependencies:
```shell
uv sync
```

3. To also install dev dependencies (pytest):
```shell
uv sync --all-extras
```

4. Add `g` to your path. What I usually do is add a bat (on Windows) that calls the script:
```bat
@echo off
uv run --project Z:\path\to\git_alias2 g %*
```

This way I can call `g` from anywhere.

### Configuring Azure CLI for DevOps
We need to tell Azure CLI that we're going to use the source control commands.
So you need to login to your Azure DevOps Organization:

```bash
az devops login
```

This will prompt for a Personal Access Token (PAT), which you can create from the Azure DevOps web portal:

1. Navigate to: https://myacc.visualstudio.com/ (replace myacc with your organization name).
2. Go to User Settings (top right) > Personal Access Tokens > New Token.
3. Generate a token with the required permissions and copy it.
4. Paste the token when prompted in the terminal.

Now configure the Default Organization:

```bash
az devops configure --defaults organization=https://myacc.visualstudio.com/
```
(Replace myacc with your organization name)

### Configuring GitLab CLI
```bash
glab auth login
```
Follow the prompts to authenticate. Only `gitlab.com` is supported (self-hosted GitLab is not supported yet).

## Commands

### `g doctor`
Checks the status of all configured CLI tools and their authentication:
```shell
g doctor
```

### `g create <repo_name>`
Creates a private repository on each provider and sets up the local repo:
1. Creates a private repo on GitHub (and any other specified providers)
2. Inits the repo in the current working directory
3. Sets the fetch URL to the first provider (GitHub by default)
4. Sets push URLs to all providers

```shell
g create my-new-repo
```

To specify which providers to use:
```shell
g create my-new-repo --providers github azure gitlab
```

Default providers: `github azure gitlab`. To change the defaults, edit `DEFAULT_PROVIDERS` in `core/providers/registry.py`.

### `g fix-create`
Detects which providers are missing from an existing repo and creates them:
```shell
g fix-create
```

Useful when a `create` partially failed (e.g., GitHub succeeded but Azure failed).

### `g disable <provider>` / `g enable <provider>`
Temporarily disable a provider (e.g., when it's down). Disabled providers are skipped in `create` and `fix-create`:
```shell
g disable gitlab
g create my-repo          # only creates on github + azure
```

Re-enable later and use `fix-create` to catch up:
```shell
g enable gitlab
g fix-create              # creates the missing gitlab repo
```

The `doctor` command shows which providers are disabled.
Config is stored in `~/.git-alias2.json`.

### `g add-remote <provider>`
Adds a single provider to an existing repository:
```shell
g add-remote gitlab
```

Options:
- `--repo-name <name>` — override auto-detected repository name
- `--set-fetch` — make this the primary fetch remote

```shell
g add-remote gitlab --repo-name my-repo --set-fetch
```

### `g tag <tag_name>`
Creates an annotated tag on the `master` branch. Checks out `master`, pulls the latest changes, then creates the tag:
```shell
g tag v1.0.0
```

Options:
- `-m, --message <message>` — custom tag message (default: `"New version: <tag_name>"`)
- `--push` — push the tag to origin after creation

```shell
g tag v1.0.0 -m "Release 1.0.0" --push
```

## Running Tests
```shell
uv run pytest
```
