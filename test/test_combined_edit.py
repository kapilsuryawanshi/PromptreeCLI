#!/usr/bin/env python3
"""
Test the new combined edit functionality
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

def test_combined_edit():
    """Test the combined edit functionality"""
    print("Testing combined edit functionality...")
    
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
        
        # Create conversations
        id1 = conversation_tree.create_conversation("First conversation", None, None)
        id2 = conversation_tree.create_conversation("Second conversation", id1, None)
        id3 = conversation_tree.create_conversation("Third conversation", None, None)  # Root conversation
        
        print(f"Created conversations: {id1} (root), {id2} (child of {id1}), {id3} (root)")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test 1: Edit both parent and subject
        print("\nTest 1: Editing both parent and subject")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id2} -parent {id3} -subject "Updated Second Subject with New Parent"')
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        # Check if both changes were made
        if "Updated parent to" in output and "Updated subject" in output:
            print("SUCCESS: Both parent and subject updated")
            # Verify the changes in the database
            updated_conv = db_manager.get_conversation(id2)
            if updated_conv and updated_conv[1] == "Updated Second Subject with New Parent" and updated_conv[5] == id3:
                print("SUCCESS: Changes correctly saved to database")
                combined_test = True
            else:
                print(f"FAILED: Data not correctly saved. Subject: {updated_conv[1] if updated_conv else 'None'}, Parent: {updated_conv[5] if updated_conv else 'None'}")
                combined_test = False
        else:
            print("FAILED: Not both parent and subject were updated")
            combined_test = False
        
        # Reset for next test
        db_manager.update_conversation_parent(id2, id1)
        db_manager.update_subject(id2, "Second conversation")
        
        # Test 2: Edit both with different order (subject first, then parent)
        print("\nTest 2: Editing both with different order (-subject first, then -parent)")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id2} -subject "New Subject for Second" -parent {id3}')
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "Updated subject" in output and "Updated parent" in output:
            print("SUCCESS: Both parameters work in different order")
            # Verify the changes in the database
            updated_conv = db_manager.get_conversation(id2)
            if updated_conv and updated_conv[1] == "New Subject for Second" and updated_conv[5] == id3:
                print("SUCCESS: Changes correctly saved to database with different order")
                order_test = True
            else:
                print(f"FAILED: Data not correctly saved. Subject: {updated_conv[1] if updated_conv else 'None'}, Parent: {updated_conv[5] if updated_conv else 'None'}")
                order_test = False
        else:
            print("FAILED: Not both parameters processed in different order")
            order_test = False
        
        # Reset for next test
        db_manager.update_conversation_parent(id2, id1)
        db_manager.update_subject(id2, "Second conversation")
        
        # Test 3: Just edit parent (backward compatibility)
        print("\nTest 3: Just edit parent (backward compatibility)")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id2} -parent None')
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "Updated parent" in output and "subject" not in output.lower():
            print("SUCCESS: Backward compatibility maintained")
            parent_only_test = True
        else:
            print("FAILED: Backward compatibility broken")
            parent_only_test = False
            
        # Reset for next test
        db_manager.update_conversation_parent(id2, id1)
        
        # Test 4: Just edit subject (backward compatibility)
        print("\nTest 4: Just edit subject (backward compatibility)")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id2} -subject "Just Subject Update"')
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "Updated subject" in output and "parent" not in output.lower():
            print("SUCCESS: Backward compatibility for subject maintained")
            subject_only_test = True
        else:
            print("FAILED: Subject-only backward compatibility broken")
            subject_only_test = False
        
        # Reset for next test
        db_manager.update_subject(id2, "Second conversation")
        
        # Test 5: Try circular reference with combined command
        print("\nTest 5: Trying circular reference with combined command")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_edit(f'{id1} -parent {id2} -subject "Test Circular"')  # Would create circular reference
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "circular reference" in output.lower():
            print("SUCCESS: Circular reference detection works with combined command")
            circular_test = True
        else:
            print("FAILED: Circular reference not detected with combined command")
            circular_test = False
        
        all_tests = [combined_test, order_test, parent_only_test, subject_only_test, circular_test]
        success_count = sum(all_tests)
        
        print(f"\nResults: {success_count}/{len(all_tests)} combined edit tests passed")
        
        return all(all_tests)
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    if test_combined_edit():
        print("\nAll combined edit functionality tests passed!")
    else:
        print("\nSome combined edit functionality tests failed!")
        sys.exit(1)