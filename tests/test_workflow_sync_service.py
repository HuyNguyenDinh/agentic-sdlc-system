import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile
import yaml

from src.core.services.workflow_sync_service import WorkflowSyncService
from src.core.ports.workflow_publisher import WorkflowPublisherPort
from src.core.domain.models import Workflow

class TestWorkflowSyncService(unittest.TestCase):
    def setUp(self):
        self.publisher = MagicMock(spec=WorkflowPublisherPort)
        self.service = WorkflowSyncService(publisher=self.publisher)
        
        self.valid_yaml_data = {
            "workflow": {
                "name": "test-workflow",
                "squad_leader": "leader-agent",
                "description": "A test workflow description"
            },
            "agents": [
                {
                    "id": "leader-agent",
                    "role": "Leader",
                    "instructions": "Lead."
                }
            ],
            "steps": [
                {
                    "id": "step-one",
                    "type": "delegate",
                    "description": "Initial delegation step",
                    "actor": "leader-agent"
                }
            ]
        }


    def test_sync_workflow_success(self):
        self.publisher.publish.return_value = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_yaml_data, f)
            temp_path = f.name
            
        try:
            success = self.service.sync_workflow(temp_path)
            self.assertTrue(success)
            
            # Verify publisher was called with correct Workflow domain object
            self.publisher.publish.assert_called_once()
            called_workflow = self.publisher.publish.call_args[0][0]
            self.assertIsInstance(called_workflow, Workflow)
            self.assertEqual(called_workflow.id, "test-workflow")
            self.assertEqual(called_workflow.description, "A test workflow description")
            self.assertIn("# Test Workflow", called_workflow.instructions)
        finally:
            os.remove(temp_path)

    def test_sync_workflow_validation_failure(self):
        invalid_yaml_data = {
            "workflow": {
                "name": "" # empty name -> validation error
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_yaml_data, f)
            temp_path = f.name
            
        try:
            success = self.service.sync_workflow(temp_path)
            self.assertFalse(success)
            self.publisher.publish.assert_not_called()
        finally:
            os.remove(temp_path)

    def test_sync_workflow_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # empty content -> safe_load returns None
            temp_path = f.name
            
        try:
            success = self.service.sync_workflow(temp_path)
            self.assertFalse(success)
            self.publisher.publish.assert_not_called()
        finally:
            os.remove(temp_path)

    def test_sync_workflow_non_existent_file(self):
        success = self.service.sync_workflow("non_existent_file_path.yaml")
        self.assertFalse(success)
        self.publisher.publish.assert_not_called()
