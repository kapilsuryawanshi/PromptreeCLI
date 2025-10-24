#!/usr/bin/env python3
"""
Test just the CLI search functionality
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def test_cli_search():
    """Test just the CLI search functionality."""
    print("Testing CLI search functionality...")
    
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
        
        # Create a conversation with "Python" in the subject
        id1 = conversation_tree.create_conversation("How to learn Python programming?", None, None)
        print(f"Created conversation with ID: {id1}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Check the actual conversation to make sure it has "Python" in it
        conv = db_manager.get_conversation(id1)
        print(f"Conversation details: ID={conv[0]}, Subject='{conv[1]}', Prompt='{conv[3]}'")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test search
        print("Testing search for 'python'...")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("python")
        output = f.getvalue()
        print(f"Search output: {repr(output)}")
        
        # Test what the database search function returns directly
        print("\nDirect database search for '%python%':")
        db_results = db_manager.search_conversations("%python%")
        print(f"Database found {len(db_results)} results")
        for result in db_results:
            print(f"  - ID: {result[0]}, Subject: {result[1]}")
        
        # What about searching for the literal term?
        print("\nDirect database search for 'python' (no wildcards):")
        db_results = db_manager.search_conversations("python")
        print(f"Database found {len(db_results)} results")
        for result in db_results:
            print(f"  - ID: {result[0]}, Subject: {result[1]}")
        
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_cli_search()