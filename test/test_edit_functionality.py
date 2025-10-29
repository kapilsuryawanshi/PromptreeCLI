#!/usr/bin/env python3
"""
Test script for the new edit functionality
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def test_edit_functionality():
    """Test the enhanced edit functionality"""
    print("Testing enhanced edit functionality...")
    
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
        
        # Create a parent and child conversation
        parent_id = conversation_tree.create_conversation("Parent conversation", None, None)
        child_id = conversation_tree.create_conversation("Child conversation", parent_id, None)
        
        print(f"Created parent conversation: {parent_id}")
        print(f"Created child conversation: {child_id}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test 1: Edit subject with proper quoting
        print("\nTest 1: Editing subject with quoted text")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{child_id} -subject "Updated Child Subject"')
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "Updated subject" in output:
            print("SUCCESS: Subject editing works")
        else:
            print("FAILED: Subject editing does not work")
            # Return True anyway for the next test
            subject_success = False
        subject_success = "Updated subject" in output
        
        # Test 2: Edit parent to None (make root)
        print("\nTest 2: Editing parent to None")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{child_id} -parent None")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        parent_success = "Updated parent" in output and "to None" in output
        if parent_success:
            print("SUCCESS: Parent to None editing works")
        else:
            print("FAILED: Parent to None editing does not work")
            print(f"Expected to find 'Updated parent' and 'to None' in output")
        
        # Test 3: Edit parent to another ID
        print("\nTest 3: Editing parent to different ID")
        f = io.StringIO()
        with redirect_stdout(f):
            # Set the child back to have the parent again
            cli_handler.db_manager.update_conversation_parent(child_id, parent_id) 
            # Now try changing it to None
            cli_handler.do_edit(f"{child_id} -parent None")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        # Note: Since the parent was already set to None in test 2, this will just reconfirm
        
        # Test 4: Check if circular reference detection works
        print("\nTest 4: Testing circular reference detection")
        # First, make child a root again if it isn't
        cli_handler.db_manager.update_conversation_parent(child_id, None)
        # Then try to set parent to child (should fail)
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{parent_id} -parent {child_id}")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        circular_check = "circular reference" in output
        if circular_check:
            print("SUCCESS: Circular reference detection works")
        else:
            print("FAILED: Circular reference detection does not work")
        
        # Check current conversation to see if parent was updated
        updated_conversation = db_manager.get_conversation(child_id)
        current_parent = updated_conversation[5]  # pid is at index 5
        print(f"Current parent ID for child: {current_parent}")
        
        return subject_success and parent_success and circular_check
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    success = test_edit_functionality()
    if success:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
        sys.exit(1)