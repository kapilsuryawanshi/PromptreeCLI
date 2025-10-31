#!/usr/bin/env python3
"""
Test for the new 'up' command functionality
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

def test_up_command_basic():
    """Test the basic functionality of the 'up' command."""
    print("Testing basic 'up' command functionality...")
    
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
        
        # Create conversation tree: root -> child
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create a root conversation
        root_id = conversation_tree.create_conversation("Root conversation prompt", None, None)
        print(f"Created root conversation with ID: {root_id}")
        
        # Create a child conversation
        child_id = conversation_tree.create_conversation("Child conversation prompt", root_id, None)
        print(f"Created child conversation with ID: {child_id}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Set the current parent to the child conversation
        cli_handler.current_parent_id = child_id
        print(f"Set current parent to child conversation (ID: {child_id})")
        
        # Test the 'up' command - should navigate to root
        import io
        from contextlib import redirect_stdout
        
        print("Testing 'up' command (should navigate from child to root)...")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_up("")
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        
        # Check that the output contains information about navigating up
        has_navigation_info = "Navigating up" in output
        has_root_subject = f"Subject for: Root conversation prompt" in output
        
        success = has_navigation_info and has_root_subject
        
        if success:
            print("SUCCESS: 'up' command navigated from child to root correctly")
            print(f"Current parent ID after 'up': {cli_handler.current_parent_id}")
            # The current parent should now be the root conversation
            parent_is_root = cli_handler.current_parent_id == root_id
            if parent_is_root:
                print("SUCCESS: Current parent ID was updated to root")
            else:
                print(f"FAILED: Expected current parent ID to be {root_id}, but got {cli_handler.current_parent_id}")
                success = False
        else:
            print("FAILED: 'up' command did not work as expected")
            print(f"Output: {repr(output)}")
            return False
        
        return success
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_up_command_no_context():
    """Test 'up' command when there's no current conversation context."""
    print("Testing 'up' command with no current context...")
    
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
        
        # Create CLI handler with no current context
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        # current_parent_id defaults to None
        
        # Test the 'up' command with no context
        import io
        from contextlib import redirect_stdout
        
        print("Testing 'up' command with no current context...")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_up("")
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        
        # Check that the output contains error message about no context
        has_error_message = "No current conversation context" in output
        
        success = has_error_message
        
        if success:
            print("SUCCESS: 'up' command properly handles no current context")
        else:
            print("FAILED: 'up' command did not handle no current context properly")
            print(f"Output: {repr(output)}")
        
        return success
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_up_command_no_parent():
    """Test 'up' command when current conversation has no parent (root level)."""
    print("Testing 'up' command with root conversation (no parent)...")
    
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
        root_id = conversation_tree.create_conversation("Root conversation prompt", None, None)
        print(f"Created root conversation with ID: {root_id}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Set the current parent to the root conversation (which has no parent)
        cli_handler.current_parent_id = root_id
        print(f"Set current parent to root conversation (ID: {root_id})")
        
        # Test the 'up' command - should fail because root has no parent
        import io
        from contextlib import redirect_stdout
        
        print("Testing 'up' command with root conversation...")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_up("")
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        
        # Check that the output contains error message about no parent
        has_error_message = "has no parent" in output or "Already at root level" in output
        
        success = has_error_message
        
        if success:
            print("SUCCESS: 'up' command properly handles root conversation (no parent)")
        else:
            print("FAILED: 'up' command did not handle root conversation properly")
            print(f"Output: {repr(output)}")
        
        return success
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_up_command_invalid_context():
    """Test 'up' command when current conversation doesn't exist."""
    print("Testing 'up' command with invalid current conversation ID...")
    
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
        
        # Set the current parent to a non-existent conversation ID
        fake_id = 999
        cli_handler.current_parent_id = fake_id
        print(f"Set current parent to fake conversation ID: {fake_id}")
        
        # Test the 'up' command - should fail because conversation doesn't exist
        import io
        from contextlib import redirect_stdout
        
        print("Testing 'up' command with invalid conversation ID...")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_up("")
        output = f.getvalue()
        
        print(f"Captured output length: {len(output)}")
        
        # Check that the output contains error message about conversation not found
        has_error_message = f"not found" in output.lower()
        
        success = has_error_message
        
        if success:
            print("SUCCESS: 'up' command properly handles invalid conversation ID")
        else:
            print("FAILED: 'up' command did not handle invalid conversation ID properly")
            print(f"Output: {repr(output)}")
        
        return success
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    print("Running tests for 'up' command functionality...\n")
    
    success1 = test_up_command_basic()
    success2 = test_up_command_no_context()
    success3 = test_up_command_no_parent()
    success4 = test_up_command_invalid_context()
    
    if success1 and success2 and success3 and success4:
        print("\nAll tests for 'up' command passed!")
    else:
        print("\nSome tests for 'up' command failed!")
        sys.exit(1)