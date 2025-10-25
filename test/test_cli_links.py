#!/usr/bin/env python
"""
Test script to verify CLI link functionality
"""
import tempfile
import os
import sys
from io import StringIO
from contextlib import redirect_stdout

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DatabaseManager
from conversation_tree import ConversationTree
from ollama_client import OllamaClient
from cli import CLIHandler

class TestCLIHandler(CLIHandler):
    """A CLI handler for testing that doesn't enter an interactive loop."""
    
    def __init__(self, db_manager, conversation_tree, model_name):
        super().__init__(db_manager, conversation_tree, model_name)
    
    def start_cli(self):
        """Override to avoid the interactive loop."""
        pass
    
    def test_edit_command(self, arg):
        """Test the edit command with different arguments."""
        # Capture the output
        f = StringIO()
        with redirect_stdout(f):
            self.do_edit(arg)
        output = f.getvalue()
        print(output)
        return output

def test_cli_functionality():
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Initialize components
        db_manager = DatabaseManager(db_path=temp_db_path)
        ollama_client = OllamaClient(model_name='test-model')  # This will be mocked
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create CLI handler
        cli_handler = TestCLIHandler(db_manager, conversation_tree, 'test-model')
        
        # Create some test conversations
        conv1_id = db_manager.add_conversation(
            subject="Test Conversation 1",
            model_name="test-model",
            user_prompt="Test prompt 1",
            llm_response="Test response 1"
        )
        print(f"Created conversation 1 with ID: {conv1_id}")
        
        conv2_id = db_manager.add_conversation(
            subject="Test Conversation 2",
            model_name="test-model",
            user_prompt="Test prompt 2",
            llm_response="Test response 2"
        )
        print(f"Created conversation 2 with ID: {conv2_id}")
        
        conv3_id = db_manager.add_conversation(
            subject="Test Conversation 3",
            model_name="test-model",
            user_prompt="Test prompt 3",
            llm_response="Test response 3"
        )
        print(f"Created conversation 3 with ID: {conv3_id}")
        
        # Test linking conversations using the edit command
        print("\n--- Testing edit command with -link option ---")
        cli_handler.test_edit_command(f"{conv1_id} -link {conv2_id},{conv3_id}")
        
        # Check if links were created
        linked_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Links for conversation {conv1_id}: {linked_ids}")
        assert conv2_id in linked_ids and conv3_id in linked_ids, "Link creation failed"
        
        # Test removing all links
        print("\n--- Testing removing all links ---")
        cli_handler.test_edit_command(f"{conv1_id} -link None")
        
        # Check if links were removed
        linked_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Links for conversation {conv1_id} after removal: {linked_ids}")
        assert len(linked_ids) == 0, "Link removal failed"
        
        # Test linking again
        print("\n--- Testing re-linking conversations ---")
        cli_handler.test_edit_command(f"{conv1_id} -link {conv2_id}")
        
        # Verify the link
        linked_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Links for conversation {conv1_id}: {linked_ids}")
        assert conv2_id in linked_ids, "Re-linking failed"
        
        print("\nAll CLI tests passed!")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_cli_functionality()