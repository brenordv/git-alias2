from unittest.mock import MagicMock, call, patch

from core.command_wrappers import tag_command


class TestTagCommand:
    @patch("core.command_wrappers.push_tag")
    @patch("core.command_wrappers.create_tag")
    @patch("core.command_wrappers.pull")
    @patch("core.command_wrappers.checkout_branch")
    @patch("core.command_wrappers.Repo")
    @patch("core.command_wrappers.is_git_repo", return_value=True)
    def test_creates_tag_with_default_message(
        self, mock_is_git, mock_repo, mock_checkout, mock_pull,
        mock_create_tag, mock_push,
    ):
        repo_instance = MagicMock()
        mock_repo.return_value = repo_instance

        tag_command("v1.0.0")

        mock_create_tag.assert_called_once_with(
            repo_instance, "v1.0.0", "New version: v1.0.0"
        )

    @patch("core.command_wrappers.push_tag")
    @patch("core.command_wrappers.create_tag")
    @patch("core.command_wrappers.pull")
    @patch("core.command_wrappers.checkout_branch")
    @patch("core.command_wrappers.Repo")
    @patch("core.command_wrappers.is_git_repo", return_value=True)
    def test_creates_tag_with_custom_message(
        self, mock_is_git, mock_repo, mock_checkout, mock_pull,
        mock_create_tag, mock_push,
    ):
        repo_instance = MagicMock()
        mock_repo.return_value = repo_instance

        tag_command("v2.0.0", message="Big release!")

        mock_create_tag.assert_called_once_with(
            repo_instance, "v2.0.0", "Big release!"
        )

    @patch("core.command_wrappers.push_tag")
    @patch("core.command_wrappers.create_tag")
    @patch("core.command_wrappers.pull")
    @patch("core.command_wrappers.checkout_branch")
    @patch("core.command_wrappers.Repo")
    @patch("core.command_wrappers.is_git_repo", return_value=True)
    def test_pushes_tag_when_flag_set(
        self, mock_is_git, mock_repo, mock_checkout, mock_pull,
        mock_create_tag, mock_push,
    ):
        repo_instance = MagicMock()
        mock_repo.return_value = repo_instance

        tag_command("v1.0.0", push=True)

        mock_push.assert_called_once_with(repo_instance, "v1.0.0")

    @patch("core.command_wrappers.push_tag")
    @patch("core.command_wrappers.create_tag")
    @patch("core.command_wrappers.pull")
    @patch("core.command_wrappers.checkout_branch")
    @patch("core.command_wrappers.Repo")
    @patch("core.command_wrappers.is_git_repo", return_value=True)
    def test_does_not_push_when_flag_not_set(
        self, mock_is_git, mock_repo, mock_checkout, mock_pull,
        mock_create_tag, mock_push,
    ):
        tag_command("v1.0.0")

        mock_push.assert_not_called()

    @patch("core.command_wrappers.push_tag")
    @patch("core.command_wrappers.create_tag")
    @patch("core.command_wrappers.pull")
    @patch("core.command_wrappers.checkout_branch")
    @patch("core.command_wrappers.Repo")
    @patch("core.command_wrappers.is_git_repo", return_value=False)
    def test_errors_when_not_git_repo(
        self, mock_is_git, mock_repo, mock_checkout, mock_pull,
        mock_create_tag, mock_push,
    ):
        tag_command("v1.0.0")

        mock_repo.assert_not_called()
        mock_checkout.assert_not_called()
        mock_create_tag.assert_not_called()

    @patch("core.command_wrappers.push_tag")
    @patch("core.command_wrappers.create_tag")
    @patch("core.command_wrappers.pull")
    @patch("core.command_wrappers.checkout_branch")
    @patch("core.command_wrappers.Repo")
    @patch("core.command_wrappers.is_git_repo", return_value=True)
    def test_checkout_and_pull_before_tag(
        self, mock_is_git, mock_repo, mock_checkout, mock_pull,
        mock_create_tag, mock_push,
    ):
        repo_instance = MagicMock()
        mock_repo.return_value = repo_instance

        # Use a shared call tracker to verify ordering
        call_order = []
        mock_checkout.side_effect = lambda *a, **kw: call_order.append("checkout")
        mock_pull.side_effect = lambda *a, **kw: call_order.append("pull")
        mock_create_tag.side_effect = lambda *a, **kw: call_order.append("create_tag")

        tag_command("v1.0.0")

        assert call_order == ["checkout", "pull", "create_tag"]
        mock_checkout.assert_called_once_with(repo_instance, "master")
        mock_pull.assert_called_once_with(repo_instance)
