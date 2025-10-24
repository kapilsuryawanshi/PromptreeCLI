#!/usr/bin/env python3
"""
Test to verify the enhanced 'open' command functionality with updated parent format
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def test_open_command_with_updated_parent_format():
    """Test the enhanced open command with updated parent conversation format."""
    print("Testing enhanced 'open' command with updated parent format...")
    
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
        
        # Test opening the child conversation - should show parent info with new format
        print(f"Testing 'open {child_id}' command:")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_open(str(child_id))
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        print(f"Does output contain ' [parent]'? {' [parent]' in output}")
        
        # Check if the output contains the expected parent marker
        has_parent_marker = " [parent]" in output
        
        if has_parent_marker:
            print("SUCCESS: Parent conversation displayed with updated format")
            # Find the parent conversation line
            lines = output.split('\n')
            parent_line = None
            for line in lines:
                if " [parent]" in line:
                    parent_line = line
                    break
            if parent_line:
                print(f"Parent line: {repr(parent_line)}")
            return True
        else:
            print("FAILED: Parent conversation not displayed with updated format")
            print(f"Full output: {repr(output)}")
            return False
            
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    print("Running test for enhanced 'open' command with updated format...\n")
    
    if test_open_command_with_updated_parent_format():
        print("\nTest passed! Updated format is now used for parent conversation display.")
    else:
        print("\nTest failed!")
        sys.exit(1)