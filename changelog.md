# Changelog

## 2.2.0
1. Declared the packages the code imports directly, `simple-log-factory` (2.0.0) and `raccoon-simple-stopwatch`, and
   dropped `raccoontools`, which nothing imported; both used to arrive only as its dependencies.
2. `g tag` reports a failed checkout of `master` (for example, local changes in the way) as an error message instead
   of a raw traceback.
3. Repository names may only contain letters, digits, spaces, `.`, `_` and `-`, and may not start with `-` or a
   space. On Windows `az` runs through a batch file, which parses its arguments with shell rules, and the CLIs read a
   leading `-` as an option.
4. Repository names detected from remotes are percent-decoded, so an Azure remote for "my repo" yields `my repo`
   instead of `my%20repo`.
5. GitLab authentication checks no longer read "not logged in" output as logged in.
6. Dev tooling moved to the `dev` dependency group (pytest, pytest-cov, ruff, mypy); `uv sync` installs it.

## 2.1.2
1. Updated dependencies.
