# Git Alias 2
This project is a collection of git "aliases" that I use frequently.
For now, I have re-implemented just the `create` command.

# Note about this project
Why use the CLI applications (gh and az) instead of the APIs? Mainly to avoid leaving tokens around with too many 
permissions. Since I already have the CLI applications installed, I can use them to create the repos without having to 
create new tokens and having to worry about leaking them (or having to renew every x days).

That being said: You need to have the GitHub (`gh`) and Azure (`az`) CLI applications installed and configured.

## Installation
1. Clone this repository
2. Install requirements
```shell
pip install -r requirements.txt
```
3. Add `g.py` to your path or somewhere you call it from anywhere.

What I usually do is to add a bat (on Windows) that calls the script to the path. Like this:
```bat
@echo off
python Z:\path\to\git_alias2\g.py %*
```

This way I can call `g` from anywhere, and it will call the script.

### Installation using VirtualEnv

If you don't already have it, install virtualenv
```shell
pip install virtualenv
```

Using `virtualenv`, create a new environment:
```shell
virtualenv venv
```

Activate the environment:
```shell
venv\Scripts\activate
```

Install the requirements:
```shell
pip install -r requirements.txt
```

#### Full script
```bash
virtualenv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Add the script to the path or create a bat file as described above, but taking into account the virtual environment:
```bat
@echo off
REM Define the project directory
set PROJECT_DIR=C:\path\to\where\you\cloned\git_alias2

REM Activate the virtual environment
call %PROJECT_DIR%\venv\Scripts\activate

REM Run the Python script using an absolute path
python %PROJECT_DIR%\script.py

REM Deactivate the virtual environment
deactivate
```

### Configuring Azure CLI for devops.
We need to tell Azure CLI that we're going to use the source control commands.
So you need to login to Your Azure DevOps Organization by using the az devops login command to authenticate:

```bash
az devops login
```

This will prompt for a Personal Access Token (PAT), which you can create from the Azure DevOps web portal:

1. Navigate to: https://myacc.visualstudio.com/ (replace myacc with your organization name).
2. Go to User Settings (top right) > Personal Access Tokens > New Token.
3. Generate a token with the required permissions and copy it.
4. Paste the token when prompted in the terminal.

Now you're logged in. Let's configure the Default Organization.

```bash
az devops configure --defaults organization=https://myacc.visualstudio.com/
```
(Replace myacc with your organization name)

Alright. Now it all should work fine.

## Commands
### Create
This will:
1. Create a private repo on github
2. Create the same repo on Azure DevOps
3. Init the repo on the `current working directory`
4. Set the fetch url to the Github repo
5. Set push urls to both, the Azure DevOps and Github repos

> Why do I need this? Well, that's a story for another day.

```shell
python g.py create <branch_name>
```
