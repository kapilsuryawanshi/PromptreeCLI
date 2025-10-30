#!/usr/bin/env python3
"""
Test to verify the updated 'open' command functionality that shows
the complete ancestor chain from root to the selected conversation.
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

def test_open_command_shows_ancestor_chain():
    """Test that the open command shows the complete ancestor chain from root to selected conversation."""
    print("Testing 'open' command shows complete ancestor chain...")
    
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
        
        # Create conversation tree: grandparent -> parent -> child
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create a grandparent conversation (root)
        grandparent_id = conversation_tree.create_conversation("This is the grandparent prompt", None, None)
        print(f"Created grandparent conversation with ID: {grandparent_id}")
        
        # Create a parent conversation
        parent_id = conversation_tree.create_conversation("This is the parent prompt", grandparent_id, None)
        print(f"Created parent conversation with ID: {parent_id}")
        
        # Create a child conversation
        child_id = conversation_tree.create_conversation("This is the child prompt", parent_id, None)
        print(f"Created child conversation with ID: {child_id}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test opening the child conversation - should show full ancestor chain
        print(f"Testing 'open {child_id}' command (should show ancestor chain):")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_open(str(child_id))
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        print(f"Full output: {repr(output)}")
        
        # Verify that all ancestors are shown in the chain
        has_grandparent = f"Subject for: This is the grandparent p" in output
        has_parent = f"Subject for: This is the parent prompt" in output
        has_child = f"Subject for: This is the child prompt" in output  # This will be in the tree
        
        # Check if the ancestor chain is properly displayed
        lines = output.strip().split('\n')
        ancestor_lines = []
        for line in lines:
            if 'Subject for:' in line and '[parent]' not in line:
                ancestor_lines.append(line)
        
        print(f"Found {len(ancestor_lines)} ancestor-related lines")
        
        # Check if grandparent, parent, and child are all in the output
        success = has_grandparent and has_parent and has_child
        
        if success:
            print("SUCCESS: Ancestor chain is displayed correctly")
            return True
        else:
            print("FAILED: Ancestor chain is NOT displayed correctly")
            print(f"Has grandparent: {has_grandparent}")
            print(f"Has parent: {has_parent}")
            print(f"Has child: {has_child}")
            return False
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_open_command_single_conversation():
    """Test the open command with a single (root) conversation."""
    print("Testing 'open' command with single root conversation...")
    
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
        
        # Create a root conversation
        root_id = conversation_tree.create_conversation("This is the root prompt", None, None)
        print(f"Created root conversation with ID: {root_id}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test opening the root conversation
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_open(str(root_id))
        output = f.getvalue()
        
        print(f"Testing 'open {root_id}' command (root conversation):")
        print(f"Captured output length: {len(output)}")
        print(f"Full output: {repr(output)}")
        
        # For a root conversation, there should be no ancestors, just the conversation itself
        has_root = f"Subject for: This is the root prompt" in output
        has_ancestor_chain = '├─ ' in output or '└─ ' in output  # Tree structure characters
        
        # The root conversation should be displayed, but not as part of an ancestor chain
        success = has_root
        
        if success:
            print("SUCCESS: Root conversation displayed correctly")
        else:
            print("FAILED: Root conversation not displayed correctly")
            return False
        
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
    print("Running tests for updated 'open' command ancestor chain functionality...\n")
    
    success1 = test_open_command_shows_ancestor_chain()
    success2 = test_open_command_single_conversation()
    success3 = test_open_command_nonexistent()
    
    if success1 and success2 and success3:
        print("\nAll tests for updated 'open' command passed!")
    else:
        print("\nSome tests for updated 'open' command failed!")
        sys.exit(1)