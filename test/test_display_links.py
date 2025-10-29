#!/usr/bin/env python
"""
Test script to verify that linked conversations are displayed when opening a conversation
"""
import tempfile
import os
from io import StringIO
from contextlib import redirect_stdout
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

def test_open_with_links():
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
            subject="Main Conversation",
            model_name="test-model",
            user_prompt="What is the capital of France?",
            llm_response="The capital of France is Paris."
        )
        print(f"Created main conversation with ID: {conv1_id}")
        
        conv2_id = db_manager.add_conversation(
            subject="Related Geography Facts",
            model_name="test-model",
            user_prompt="Tell me about European capitals",
            llm_response="Paris is the capital of France, Berlin is the capital of Germany, etc."
        )
        print(f"Created related conversation with ID: {conv2_id}")
        
        conv3_id = db_manager.add_conversation(
            subject="French Culture",
            model_name="test-model",
            user_prompt="What are some French cultural aspects?",
            llm_response="French culture includes art, cuisine, fashion, and architecture."
        )
        print(f"Created French culture conversation with ID: {conv3_id}")
        
        # Link the main conversation to the other two
        db_manager.add_conversation_link(conv1_id, conv2_id)
        db_manager.add_conversation_link(conv1_id, conv3_id)
        print(f"Linked conversation {conv1_id} to {conv2_id} and {conv3_id}")
        
        # Capture the output of the open command
        # We'll temporarily replace the print function with a custom one to capture output
        original_print = print
        captured_output = []
        
        def capture_print(*args, **kwargs):
            captured_output.append(' '.join(map(str, args)))
        
        # Replace print with our capturing function
        import builtins
        builtins.print = capture_print
        
        try:
            # This will print to our capturing function instead of the console
            tree = db_manager.get_conversation_tree(conv1_id)
            if tree:
                cli_handler._print_conversation_tree(tree, show_full_content=True)
        finally:
            # Restore the original print function
            builtins.print = original_print
        
        output = '\n'.join(captured_output)
        
        print("\n--- Output of open command ---")
        original_print(output)
        
        # Verify that linked conversations are displayed
        assert "Linked conversations:" in output, "Linked conversations section not found in output"
        assert f"id: {conv2_id}" in output, f"Linked conversation {conv2_id} not found in output"
        assert f"id: {conv3_id}" in output, f"Linked conversation {conv3_id} not found in output"
        
        print("Test passed! Linked conversations are properly displayed when opening a conversation.")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_open_with_links()