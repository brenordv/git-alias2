#  Upgrade Plan

## Replace `virtualenv` with `uv`, adding `pyproject.toml`, and `uv.lock`.
<add effort, steps required, and if it is worth it>

## Update packages
Packages on this project are probably out of date.
<add effort, steps required, and if it is worth it>

## Add tests
<add effort, steps required, and if it is worth it>

## Modernize code syntax
<add effort, steps required, and if it is worth it>

## Review for bugs
<add effort, steps required, and if it is worth it>

## Review the modus-operandi
The app requires physical cli tools to be installed. This has the advantage of not requiring API keys, tokens or any
credentials to be present. However, it also means we have extra steps.
Is it worth to keep using them, or should we switch to a more SDK/package, or even direct API call approach?
<add effort, steps required, and if it is worth it>

## Add error fix suggestions
If the app fails, we could suggest how to fix it, especially if still using the physical cli tools.
<add effort, steps required, and if it is worth it>

## Add the command `fix-create`
This will analyze the remote repos, and add the missing ones, leaving GitHub as the default for pull.
<add effort, steps required, and if it is worth it>

## Add support for GitLab. 
This would need to create the project on GitLab, and then add it as a remote repo.
<add effort, steps required, and if it is worth it>

## Add `add-remote <provider>`
This command will run the routine to add the remote repo for the provider (github, azure devops, gitlab, etc).
For this to work, the provider must be supported.