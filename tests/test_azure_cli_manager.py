import json
from unittest.mock import patch

import pytest

from core.exceptions import RepoCreationError
from core.providers.azure import AzureDevOpsProvider


class TestAzureProviderCheckAuth:
    @patch("core.providers.azure.run_cli")
    def test_logged_in(self, mock_run):
        mock_run.return_value = _make_result(
            stdout=json.dumps({"value": [{"name": "proj1"}, {"name": "proj2"}]})
        )
        provider = AzureDevOpsProvider()
        is_auth, msg = provider.check_auth()
        assert is_auth is True
        assert "2 project(s)" in msg

    @patch("core.providers.azure.run_cli")
    def test_logged_in_empty_projects(self, mock_run):
        mock_run.return_value = _make_result(
            stdout=json.dumps({"value": []})
        )
        provider = AzureDevOpsProvider()
        is_auth, msg = provider.check_auth()
        assert is_auth is True
        assert "0 project(s)" in msg

    @patch("core.providers.azure.run_cli")
    def test_not_logged_in(self, mock_run):
        mock_run.return_value = _make_result(stdout="not json output")
        provider = AzureDevOpsProvider()
        is_auth, msg = provider.check_auth()
        assert is_auth is False

    @patch("core.providers.azure.run_cli")
    def test_malformed_json(self, mock_run):
        mock_run.return_value = _make_result(stdout="{malformed")
        provider = AzureDevOpsProvider()
        is_auth, msg = provider.check_auth()
        assert is_auth is False


class TestAzureProviderGetRemoteUrl:
    @patch("core.providers.azure.run_cli")
    def test_valid_json(self, mock_run):
        mock_run.return_value = _make_result(
            stdout=json.dumps({"remoteUrl": "https://dev.azure.com/org/proj/_git/repo"})
        )
        provider = AzureDevOpsProvider()
        url = provider.get_remote_url("repo")
        assert url == "https://dev.azure.com/org/proj/_git/repo"

    @patch("core.providers.azure.run_cli")
    def test_invalid_json(self, mock_run):
        mock_run.return_value = _make_result(stdout="not json")
        provider = AzureDevOpsProvider()
        with pytest.raises(RepoCreationError):
            provider.get_remote_url("repo")

    @patch("core.providers.azure.run_cli")
    def test_missing_remote_url_field(self, mock_run):
        mock_run.return_value = _make_result(
            stdout=json.dumps({"id": "abc", "name": "repo"})
        )
        provider = AzureDevOpsProvider()
        with pytest.raises(RepoCreationError):
            provider.get_remote_url("repo")


class TestAzureProviderCreateRepo:
    @patch.object(AzureDevOpsProvider, "get_remote_url")
    @patch("core.providers.azure.run_cli")
    def test_success(self, mock_run, mock_get_url):
        mock_run.return_value = _make_result(
            stdout=json.dumps({
                "id": "abc-123",
                "name": "my-repo",
                "state": "wellFormed",
            })
        )
        mock_get_url.return_value = "https://dev.azure.com/org/my-repo/_git/my-repo"

        provider = AzureDevOpsProvider()
        url = provider.create_repo("my-repo")
        assert url == "https://dev.azure.com/org/my-repo/_git/my-repo"

    @patch("core.providers.azure.run_cli")
    def test_bad_state(self, mock_run):
        mock_run.return_value = _make_result(
            stdout=json.dumps({
                "id": "abc-123",
                "name": "my-repo",
                "state": "failed",
            })
        )
        provider = AzureDevOpsProvider()
        with pytest.raises(RepoCreationError, match="State: failed"):
            provider.create_repo("my-repo")

    @patch("core.providers.azure.run_cli")
    def test_invalid_json_response(self, mock_run):
        mock_run.return_value = _make_result(stdout="error text")
        provider = AzureDevOpsProvider()
        with pytest.raises(RepoCreationError):
            provider.create_repo("my-repo")


def _make_result(stdout="", stderr="", returncode=0):
    from subprocess import CompletedProcess
    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)
