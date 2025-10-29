#!/usr/bin/env python3
"""
Simple test to verify the enhanced 'open' command functionality
that shows parent conversation subject before the current conversation.
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

def test_open_command_with_parent():
    """Test the enhanced open command with parent conversation."""
    print("Testing enhanced 'open' command with parent conversation...")
    
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
        
        # Create conversation tree: parent -> child
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create a parent conversation
        parent_id = conversation_tree.create_conversation("This is the parent prompt", None, None)
        print(f"Created parent conversation with ID: {parent_id}")
        
        # Create a child conversation
        child_id = conversation_tree.create_conversation("This is the child prompt", parent_id, None)
        print(f"Created child conversation with ID: {child_id}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test opening the child conversation - should show parent info
        print(f"Testing 'open {child_id}' command:")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_open(str(child_id))
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        print(f"Does output contain ' [parent]'? {' [parent]' in output}")
        
        # Verify that the parent conversation subject is displayed with new format
        has_parent_info = " [parent]" in output
        
        if has_parent_info:
            print("SUCCESS: Parent conversation subject is displayed with new format")
        else:
            print("FAILED: Parent conversation subject is NOT displayed")
            print(f"Full output: {repr(output)}")
            return False
            
        # Test opening the parent conversation - should NOT show parent info (since it has no parent)
        print(f"Testing 'open {parent_id}' command (no parent):")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_open(str(parent_id))
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        print(f"Does output contain ' [parent]'? {' [parent]' in output}")
        
        # Since parent has no parent, there shouldn't be a "[parent]" line
        if " [parent]" not in output:
            print("SUCCESS: No parent shown for root conversation")
        else:
            print("FAILED: Unexpected parent shown for root conversation")
            print(f"Full output: {repr(output)}")
            return False
        
        print("All tests passed!")
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_open_command_nonexistent():
    """Test the open command with non-existent conversation ID."""
    print("Testing 'open' command with non-existent conversation ID...")
    
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
        
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Test with non-existent ID
        import io
        from contextlib import redirect_stdout
        
        nonexistent_id = 999
        print(f"Testing 'open {nonexistent_id}' command:")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_open(str(nonexistent_id))
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        print(f"Does output contain 'not found'? {'not found' in output.lower()}")
        
        if "not found" in output.lower():
            print("SUCCESS: Correctly handles non-existent conversation ID")
        else:
            print("FAILED: Did not handle non-existent conversation ID properly")
            print(f"Full output: {repr(output)}")
            return False
        
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    print("Running tests for enhanced 'open' command functionality...\n")
    
    success1 = test_open_command_with_parent()
    success2 = test_open_command_nonexistent()
    
    if success1 and success2:
        print("\nAll tests for enhanced 'open' command passed!")
    else:
        print("\nSome tests for enhanced 'open' command failed!")
        sys.exit(1)