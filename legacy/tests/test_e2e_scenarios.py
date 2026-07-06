"""End-to-end tests for Nexus Agents and Execution Engine."""

import unittest
from unittest.mock import MagicMock, patch
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from core.models.tool_context import ToolContext
from core.models.instruction import Instruction
from agents.registry import CapabilityRegistry
from agents.orchestrator import Orchestrator
from engine.execution_engine import ExecutionEngine
from engine.transaction import TransactionManager
from engine.approval import MockApprovalProvider

# Import agents
from agents.file_agent import FileAgent
from agents.code_agent import CodeAgent
from agents.terminal_agent import TerminalAgent
from agents.os_agent import OSAgent

class TestE2EScenarios(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()
        self.registry.register_agent(FileAgent())
        self.registry.register_agent(CodeAgent())
        self.registry.register_agent(TerminalAgent())
        self.registry.register_agent(OSAgent())
        
        self.tx_manager = TransactionManager()
        self.engine = ExecutionEngine(
            transaction_manager=self.tx_manager,
            approval_provider=MockApprovalProvider(approve=True)
        )
        self.orchestrator = Orchestrator(registry=self.registry, engine=self.engine)
        
    def test_code_refactoring_scenario(self):
        """Test reading an AST and then editing a file."""
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_code.py"
            test_file.write_text("def hello():\n    return 'world'", encoding='utf-8')
            
            ctx = ToolContext(transaction_id="tx-123", working_directory=temp_dir)
            
            ast_instr = {
                "agent_name": "code_agent",
                "intent": "read_ast",
                "parameters": {"file_path": str(test_file), "target_node": "hello"}
            }
            ast_results = self.orchestrator.execute_instruction(ast_instr["agent_name"], ast_instr, ctx)
            self.assertTrue(ast_results[0].success)
            self.assertIn("def hello():", ast_results[0].output)
            
            # 2. Edit File
            edit_instr = {
                "agent_name": "code_agent",
                "intent": "edit_file",
                "parameters": {
                    "file_path": str(test_file),
                    "target_content": "return 'world'",
                    "replacement_content": "return 'nexus'"
                }
            }
            edit_results = self.orchestrator.execute_instruction(edit_instr["agent_name"], edit_instr, ctx)
            self.assertTrue(edit_results[0].success)
            
            # Verify Edit
            self.assertIn("return 'nexus'", test_file.read_text(encoding='utf-8'))
            
            # 3. Rollback Edit
            self.engine.abort("tx-123")
            
            # Verify Rollback
            self.assertIn("return 'world'", test_file.read_text(encoding='utf-8'))

    def test_os_and_terminal_scenario(self):
        """Test retrieving sysinfo and running a benign command."""
        ctx = ToolContext(transaction_id="tx-456", working_directory=".")
        
        # 1. OS Agent
        os_instr = {
                "agent_name": "os_agent",
                "intent": "get_system_info",
                "parameters": {}
        }
        os_results = self.orchestrator.execute_instruction(os_instr["agent_name"], os_instr, ctx)
        self.assertTrue(os_results[0].success)
        self.assertIn("OS:", os_results[0].output)
        
        # 2. Terminal Agent
        term_instr = {
                "agent_name": "terminal_agent",
                "intent": "run_command",
                "parameters": {"command": "echo 'Nexus'"}
        }
        term_results = self.orchestrator.execute_instruction(term_instr["agent_name"], term_instr, ctx)
        self.assertTrue(term_results[0].success)
        self.assertIn("Nexus", term_results[0].output)

if __name__ == '__main__':
    unittest.main()
