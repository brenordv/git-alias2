# Git Alias 2
This project is a collection of git "aliases" that I use frequently.
For now, I have re-implemented just the `create` command.

# Note about this project
Why use the CLI applications (gh and az) instead of the APIs? Mainly to avoid leaving tokens around with too many 
permissions. Since I already have the CLI applications installed, I can use them to create the repos without having to 
create new tokens and having to worry about leaking them (or having to renew every x days).

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

This way I can call `g` from anywhere and it will call the script.


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
