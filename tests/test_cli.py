import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from src.adapters.cli.entrypoint import main

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

if __name__ == "__main__":
    unittest.main()
