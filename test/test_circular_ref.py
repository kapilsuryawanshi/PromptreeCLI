#!/usr/bin/env python3
"""
Test the circular reference detection specifically
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def test_circular_reference():
    """Test just the circular reference detection"""
    print("Testing circular reference detection...")
    
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
        
        # Create a chain: 1 -> 2 -> 3  (1 is parent of 2, 2 is parent of 3)
        id1 = conversation_tree.create_conversation("First conversation", None, None)
        id2 = conversation_tree.create_conversation("Second conversation", id1, None)
        id3 = conversation_tree.create_conversation("Third conversation", id2, None)
        
        print(f"Created conversation chain: {id1} -> {id2} -> {id3}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Test the circular reference detection function directly
        print(f"\nTesting if {id3} can become parent of {id1} (should be circular):")
        is_circular = cli_handler._would_create_circular_reference(id1, id3)
        print(f"Result: {is_circular}")
        
        if is_circular:
            print("SUCCESS: Correctly detected circular reference")
        else:
            print("FAILED: Did not detect circular reference")
            return False
        
        print(f"\nTesting if {id1} can become parent of {id3} (should be OK):")
        is_circular = cli_handler._would_create_circular_reference(id3, id1)
        print(f"Result: {is_circular}")
        
        if not is_circular:
            print("SUCCESS: Correctly allowed non-circular reference")
        else:
            print("FAILED: Incorrectly detected circular reference")
            return False
        
        # Test same ID (should be circular)
        print(f"\nTesting if {id1} can become parent of itself (should be circular):")
        is_circular = cli_handler._would_create_circular_reference(id1, id1)
        print(f"Result: {is_circular}")
        
        if is_circular:
            print("SUCCESS: Correctly detected self-reference as circular")
        else:
            print("FAILED: Did not detect self-reference as circular")
            return False
        
        # Test with unrelated conversation (should be OK)
        id4 = conversation_tree.create_conversation("Fourth conversation", None, None)
        print(f"\nTesting if {id4} can become parent of {id1} (should be OK):")
        is_circular = cli_handler._would_create_circular_reference(id1, id4)
        print(f"Result: {is_circular}")
        
        if not is_circular:
            print("SUCCESS: Correctly allowed unrelated conversation as parent")
        else:
            print("FAILED: Incorrectly detected unrelated as circular")
            return False
            
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    if test_circular_reference():
        print("\nAll circular reference tests passed!")
    else:
        print("\nSome circular reference tests failed!")
        sys.exit(1)