#!/usr/bin/env python3
"""
Final comprehensive test of all edit functionality
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def test_all_edit_features():
    """Test all edit functionality comprehensively"""
    print("Testing all edit functionality comprehensively...")
    
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
        
        # Create conversations: 1 -> 2 -> 3
        id1 = conversation_tree.create_conversation("First conversation", None, None)
        id2 = conversation_tree.create_conversation("Second conversation", id1, None)
        id3 = conversation_tree.create_conversation("Third conversation", id2, None)
        
        print(f"Created conversation chain: {id1} -> {id2} -> {id3}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test 1: Edit subject
        print("\nTest 1: Editing subject")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id2} -subject "Updated Second Subject"')
        output = f.getvalue()
        
        if "Updated subject for conversation 2 to:" in output:
            print("SUCCESS: Subject editing works")
            subject_test = True
        else:
            print("FAILED: Subject editing failed")
            subject_test = False
        
        # Test 2: Edit parent to None (make root)
        print("\nTest 2: Editing parent to None")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{id2} -parent None")
        output = f.getvalue()
        
        if "Updated parent for conversation 2 to None (now root conversation)" in output:
            print("SUCCESS: Parent to None editing works")
            parent_none_test = True
        else:
            print("FAILED: Parent to None editing failed")
            parent_none_test = False
        
        # Reset parent for next test
        db_manager.update_conversation_parent(id2, id1)
        
        # Test 3: Edit parent to different valid ID
        print("\nTest 3: Editing parent to different valid ID")
        id4 = conversation_tree.create_conversation("Fourth conversation (root)", None, None)
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{id2} -parent {id4}")
        output = f.getvalue()
        
        if f"Updated parent for conversation 2 to {id4}." in output:
            print("SUCCESS: Parent to different ID editing works")
            parent_id_test = True
        else:
            print("FAILED: Parent to different ID editing failed")
            print(f"Output was: {repr(output)}")
            parent_id_test = False
        
        # Reset parent for next test
        db_manager.update_conversation_parent(id2, id1)
        
        # Test 4: Attempt circular reference (should fail)
        print("\nTest 4: Attempting circular reference (should fail)")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{id1} -parent {id2}")  # Trying to make 1's parent be 2 (who is child of 1)
        output = f.getvalue()
        
        if "circular reference" in output.lower():
            print("SUCCESS: Circular reference detection works")
            circular_test = True
        else:
            print("FAILED: Circular reference detection failed")
            print(f"Output was: {repr(output)}")
            circular_test = False
        
        # Test 5: Attempt invalid parent ID (should fail)
        print("\nTest 5: Attempting invalid parent ID (should fail)")
        invalid_id = 999
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{id1} -parent {invalid_id}")
        output = f.getvalue()
        
        if "not found" in output.lower():
            print("SUCCESS: Invalid parent ID detection works")
            invalid_test = True
        else:
            print("FAILED: Invalid parent ID detection failed")
            print(f"Output was: {repr(output)}")
            invalid_test = False
        
        # Test 6: Attempt editing non-existent conversation (should fail)
        print("\nTest 6: Attempting to edit non-existent conversation (should fail)")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f"{999} -subject \"Some new subject\"")
        output = f.getvalue()
        
        if "not found" in output.lower():
            print("SUCCESS: Non-existent conversation detection works")
            nonexistent_test = True
        else:
            print("FAILED: Non-existent conversation detection failed")
            print(f"Output was: {repr(output)}")
            nonexistent_test = False
        
        # Check final state
        final_conv = db_manager.get_conversation(id2)
        print(f"\nFinal state: Conversation {id2} has parent ID: {final_conv[5]}")
        
        all_tests = [subject_test, parent_none_test, parent_id_test, circular_test, invalid_test, nonexistent_test]
        success_count = sum(all_tests)
        
        print(f"\nResults: {success_count}/{len(all_tests)} tests passed")
        
        return all(all_tests)
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    if test_all_edit_features():
        print("\nAll edit functionality tests passed!")
    else:
        print("\nSome edit functionality tests failed!")
        sys.exit(1)