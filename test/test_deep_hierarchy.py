#!/usr/bin/env python3
"""
Test with deeper hierarchy to verify ancestor chain tree structure
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

def test_deep_hierarchy():
    """Create a deeper hierarchy to test the tree structure."""
    print("Testing deeper ancestor chain...")
    
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
        
        # Create conversation tree: root -> level1 -> level2 -> target
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create a root conversation
        root_id = conversation_tree.create_conversation("Root conversation prompt", None, None)
        print(f"Created root conversation with ID: {root_id}")
        
        # Create level 1 conversation
        level1_id = conversation_tree.create_conversation("Level 1 conversation prompt", root_id, None)
        print(f"Created level 1 conversation with ID: {level1_id}")
        
        # Create level 2 conversation
        level2_id = conversation_tree.create_conversation("Level 2 conversation prompt", level1_id, None)
        print(f"Created level 2 conversation with ID: {level2_id}")
        
        # Create target conversation
        target_id = conversation_tree.create_conversation("Target conversation prompt", level2_id, None)
        print(f"Created target conversation with ID: {target_id}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Test opening the target conversation (should show full ancestor chain)
        print(f"\nOpening target conversation (ID: {target_id}):")
        print("=" * 50)
        cli_handler.do_open(str(target_id))
        print("=" * 50)

        print("\nDeep hierarchy test completed successfully!")
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_deep_hierarchy()