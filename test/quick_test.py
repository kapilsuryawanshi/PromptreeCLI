#!/usr/bin/env python3
"""
Quick test to verify edit functionality works with the new format
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def quick_test():
    """Quick test of basic functionality"""
    print("Quick test of edit functionality...")
    
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
        
        # Create conversation
        id1 = conversation_tree.create_conversation("First conversation", None, None)
        
        print(f"Created conversation: {id1}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test 1: Edit subject
        print("\nTest 1: Editing subject")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id1} -subject "Updated Subject"')
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "Updated conversation" in output and "Updated subject" in output:
            print("SUCCESS: Subject editing works with new format")
            subject_ok = True
        else:
            print("FAILED: Subject editing failed")
            subject_ok = False
        
        # Test 2: Edit parent to None
        print("\nTest 2: Editing parent to None")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{id1} -parent None")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "Updated conversation" in output and "to None" in output:
            print("SUCCESS: Parent to None editing works with new format")
            parent_ok = True
        else:
            print("FAILED: Parent to None editing failed")
            parent_ok = False
        
        # Verify it was saved to DB
        updated_conv = db_manager.get_conversation(id1)
        if updated_conv and updated_conv[5] is None:  # Parent should be None
            print("SUCCESS: Parent correctly saved to database")
        else:
            print(f"FAILED: Parent not correctly saved. Current parent: {updated_conv[5] if updated_conv else 'None'}")
        
        # Reset parent for next test
        db_manager.update_conversation_parent(id1, None)  # id1 was originally root anyway
        
        # Test 3: Combined edit
        id2 = conversation_tree.create_conversation("Second conversation", None, None)
        print(f"\nTest 3: Combined edit for new conversation {id2}")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id2} -subject "Combined Subject" -parent {id1}')
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "Updated conversation" in output and "Updated subject" in output and "Updated parent" in output:
            print("SUCCESS: Combined edit works")
        else:
            print("FAILED: Combined edit failed")
        
        # Verify combined changes were saved
        updated_conv2 = db_manager.get_conversation(id2)
        if (updated_conv2 and 
            updated_conv2[1] == "Combined Subject" and 
            updated_conv2[5] == id1):
            print("SUCCESS: Combined changes correctly saved to database")
        else:
            print(f"FAILED: Combined changes not correctly saved. Subject: {updated_conv2[1] if updated_conv2 else 'None'}, Parent: {updated_conv2[5] if updated_conv2 else 'None'}")
        
        all_ok = subject_ok and parent_ok and combined_ok
        return all_ok
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    if quick_test():
        print("\nAll quick tests passed!")
    else:
        print("\nSome quick tests failed!")
        sys.exit(1)