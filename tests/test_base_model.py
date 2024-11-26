"""Unit tests for base_model.py"""

import unittest
from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import START

from langchain_app.base_model import State, call_model, workflow


class TestBaseModel(unittest.TestCase):
    """Test cases for base_model.py functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_state = State(
            input="test question",
            chat_history=[],
            context="test context",
            answer=""
        )

    def test_state_class(self):
        """Test State class initialization and typing"""
        self.assertEqual(self.test_state["input"], "test question")
        self.assertEqual(self.test_state["chat_history"], [])
        self.assertEqual(self.test_state["context"], "test context")
        self.assertEqual(self.test_state["answer"], "")

    @patch('langchain_app.base_model.rag_chain')
    def test_call_model(self, mock_rag_chain):
        """Test call_model function"""
        # Mock the rag_chain response
        mock_rag_chain.invoke.return_value = {
            "answer": "test answer",
            "context": "test context"
        }

        result = call_model(self.test_state)

        # Verify rag_chain was called with correct state
        mock_rag_chain.invoke.assert_called_once_with(self.test_state)

        # Check response structure
        self.assertIn("chat_history", result)
        self.assertIn("context", result)
        self.assertIn("answer", result)

        # Verify chat history format
        self.assertEqual(len(result["chat_history"]), 2)
        self.assertIsInstance(result["chat_history"][0], HumanMessage)
        self.assertIsInstance(result["chat_history"][1], AIMessage)
        
        # Verify content
        self.assertEqual(result["chat_history"][0].content, "test question")
        self.assertEqual(result["chat_history"][1].content, "test answer")
        self.assertEqual(result["context"], "test context")
        self.assertEqual(result["answer"], "test answer")

    def test_workflow_structure(self):
        """Test workflow graph structure"""
        # Verify workflow has expected nodes
        self.assertIn("model", workflow.nodes)

        # Verify START edge exists
        edges = workflow.edges
        start_edges = [edge for edge in edges if edge[0] == START]
        self.assertTrue(any(edge[1] == "model" for edge in start_edges))


if __name__ == '__main__':
    unittest.main()