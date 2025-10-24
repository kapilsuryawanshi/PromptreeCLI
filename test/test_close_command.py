#!/usr/bin/env python3
"""
Test to verify the new 'close' command functionality
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the parent directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from database import DatabaseManager
from cli import CLIHandler

def test_close_command():
    """Test the new close command functionality."""
    print("Testing 'close' command functionality...")
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name

    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Mock Ollama client to avoid requiring Ollama service
        class MockOllamaClient:
            def __init__(self, model_name):
                self.model_name = model_name
            
            def generate_response(self, prompt, context=None, stream_callback=None):
                return f"Mock response to: {prompt}"
                
            def generate_subject(self, prompt, response):
                return f"Subject for: {prompt[:30]}..."
        
        # Create conversation tree
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Create a conversation to set as current parent
        parent_id = conversation_tree.create_conversation("This is the parent prompt", None, None)
        print(f"Created parent conversation with ID: {parent_id}")
        
        # Manually set the current parent ID to simulate having an open conversation
        cli_handler.current_parent_id = parent_id
        print(f"Set current parent ID to: {cli_handler.current_parent_id}")
        
        # Verify current parent is set
        assert cli_handler.current_parent_id == parent_id, "Current parent should be set"
        print("Verified current parent is set")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test the close command
        print("Testing 'close' command:")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_close("")
        output = f.getvalue()
        
        print(f"Captured output: {repr(output)}")
        
        # Check that the current_parent_id was reset to None
        if cli_handler.current_parent_id is None:
            print("SUCCESS: current_parent_id was reset to None")
        else:
            print(f"FAILED: current_parent_id is still {cli_handler.current_parent_id}, should be None")
            return False
        
        # Check that appropriate message was printed
        if "Current conversation context closed" in output:
            print("SUCCESS: Appropriate message was printed")
        else:
            print("FAILED: Expected message was not printed")
            return False
        
        print("All tests passed!")
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_close_command_with_arg():
    """Test the close command with an argument (should ignore it)."""
    print("\nTesting 'close' command with argument...")
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name

    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Mock Ollama client
        class MockOllamaClient:
            def __init__(self, model_name):
                self.model_name = model_name
            
            def generate_response(self, prompt, context=None, stream_callback=None):
                return f"Mock response to: {prompt}"
                
            def generate_subject(self, prompt, response):
                return f"Subject for: {prompt[:30]}..."
        
        # Create conversation tree
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Set current parent ID
        cli_handler.current_parent_id = 123
        
        # Test close command with argument
        cli_handler.do_close("some argument")
        
        # Should still reset to None regardless of argument
        if cli_handler.current_parent_id is None:
            print("SUCCESS: current_parent_id was reset to None even with argument")
            return True
        else:
            print("FAILED: current_parent_id was not reset")
            return False
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    print("Running tests for 'close' command functionality...\n")
    
    success1 = test_close_command()
    success2 = test_close_command_with_arg()
    
    if success1 and success2:
        print("\nAll tests for 'close' command passed!")
    else:
        print("\nSome tests for 'close' command failed!")
        sys.exit(1)