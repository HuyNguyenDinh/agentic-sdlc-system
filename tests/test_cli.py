import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from src.adapters.cli.entrypoint import main
from src.bootstrap_obsidian_wiki import DEFAULT_VAULT_PATH

class TestCLI(unittest.TestCase):
    @patch("src.adapters.cli.entrypoint.WorkflowSyncService")
    @patch("src.adapters.cli.entrypoint.MulticaAdapter")
    @patch("src.adapters.cli.entrypoint.Path.exists")
    def test_sync_workflow_cli_success(self, mock_exists, mock_adapter_cls, mock_service_cls):
        mock_exists.return_value = True
        mock_service = MagicMock()
        mock_service.sync_workflow.return_value = True
        mock_service_cls.return_value = mock_service
        
        test_args = ["cli.py", "sync-workflow", "workflow.yaml", "--runtime-id", "test-rt"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            
        mock_adapter_cls.assert_called_once_with(runtime_id="test-rt")
        mock_service.sync_workflow.assert_called_once_with("workflow.yaml")

    @patch("src.adapters.cli.entrypoint.Path.exists")
    def test_sync_workflow_cli_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        
        test_args = ["cli.py", "sync-workflow", "non_existent.yaml"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)

    @patch("src.adapters.cli.entrypoint.run_bootstrap")
    def test_bootstrap_wiki_cli_success(self, mock_run_bootstrap):
        test_args = [
            "cli.py",
            "bootstrap-wiki",
            "--repo",
            "org/private-kb",
            "--non-interactive",
            "--dry-run",
        ]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        self.assertTrue(mock_run_bootstrap.called)

    @patch("src.adapters.cli.entrypoint.run_bootstrap_gitnexus")
    def test_bootstrap_gitnexus_cli_monorepo_mode(self, mock_run_bootstrap_gitnexus):
        test_args = [
            "cli.py",
            "bootstrap-gitnexus",
            "--mode",
            "monorepo",
            "--repo",
            "org/private-repo",
            "--dry-run",
        ]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        mock_run_bootstrap_gitnexus.assert_called_once()

    @patch("src.adapters.cli.entrypoint.run_bootstrap_gitnexus")
    def test_bootstrap_gitnexus_cli_multi_repo_mode(self, mock_run_bootstrap_gitnexus):
        test_args = [
            "cli.py",
            "bootstrap-gitnexus",
            "--mode",
            "multi-repo",
            "--repos",
            "org/repo-a",
            "org/repo-b",
            "--group-name",
            "my-team",
            "--dry-run",
        ]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        mock_run_bootstrap_gitnexus.assert_called_once()

    @patch("src.adapters.cli.entrypoint.run_sync_workflow")
    @patch("src.adapters.cli.entrypoint.run_sync_agent")
    @patch("src.adapters.cli.entrypoint.install_gitnexus")
    @patch("src.adapters.cli.entrypoint.install_skills_from_file")
    @patch("src.adapters.cli.entrypoint.run_bootstrap")
    def test_bootstrap_cli_success(self, mock_run_bootstrap, mock_install_skills, mock_install_gitnexus, mock_run_sync_agent, mock_run_sync_workflow):
        test_args = [
            "cli.py",
            "bootstrap",
            "--repo",
            "org/private-kb",
            "--workflow",
            "workflow.yaml",
            "--dry-run",
        ]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        mock_run_bootstrap.assert_called_once()
        mock_install_skills.assert_called_once()
        mock_install_gitnexus.assert_called_once_with(dry_run=True)
        mock_run_sync_agent.assert_called_once()
        mock_run_sync_workflow.assert_called_once()

    @patch("src.adapters.cli.entrypoint.install_skills_from_file")
    @patch("src.adapters.cli.entrypoint.run_bootstrap")
    def test_bootstrap_cli_error_returns_1(self, mock_run_bootstrap, mock_install_skills):
        mock_install_skills.side_effect = RuntimeError("skills failed")
        test_args = ["cli.py", "bootstrap", "--repo", "org/private-kb", "--dry-run"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)

        mock_run_bootstrap.assert_called_once()

    @patch("src.adapters.cli.entrypoint.run_bootstrap")
    def test_bootstrap_wiki_cli_error_returns_1(self, mock_run_bootstrap):
        mock_run_bootstrap.side_effect = RuntimeError("Repository is required")
        test_args = ["cli.py", "bootstrap-wiki", "--non-interactive"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)

    @patch("src.adapters.cli.entrypoint.run_post_bootstrap_check")
    def test_check_bootstrap_cli_success(self, mock_check):
        test_args = [
            "cli.py",
            "check-wiki-bootstrap",
            "--repo",
            "org/private-kb",
            "--branch",
            "main",
        ]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

        self.assertTrue(mock_check.called)

    @patch("src.adapters.cli.entrypoint.run_post_bootstrap_check")
    def test_check_bootstrap_cli_error_returns_1(self, mock_check):
        mock_check.side_effect = RuntimeError("Managed cron sync entry was not found in crontab")
        test_args = ["cli.py", "check-wiki-bootstrap", "--repo", "org/private-kb"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
