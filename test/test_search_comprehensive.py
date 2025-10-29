#!/usr/bin/env python3
"""
Final test to verify the search command works correctly with all features
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def test_search_comprehensive():
    """Comprehensive test of search functionality."""
    print("Testing comprehensive search functionality...")
    
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
        
        # Create test conversations
        id1 = conversation_tree.create_conversation("Python programming basics", None, None)  # Subject contains "Python"
        id2 = conversation_tree.create_conversation("JavaScript tutorial", None, None)       # Subject contains "JavaScript"
        id3 = conversation_tree.create_conversation("Learning Java and JavaScript", None, None)  # Subject contains both
        id4 = conversation_tree.create_conversation("Advanced Python concepts", None, None)      # Subject contains "Python"
        
        print(f"Created conversations with IDs: {id1}, {id2}, {id3}, {id4}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test 1: Case-insensitive search for "python"
        print("\nTest 1: Case-insensitive search for 'python'")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("python")
        output = f.getvalue()
        print(f"Output contains {output.count('Found')} match(es)")
        
        # Should find 2 conversations (id1 and id4)
        if "Found 2 conversation(s)" in output:
            print("SUCCESS: Found 2 conversations for 'python' search")
        else:
            print(f"FAILED: Expected 2 conversations, got different result")
            print(f"Output: {repr(output)}")
            return False
        
        # Test 2: Wildcard search "*script*"
        print("\nTest 2: Wildcard search '*script*'")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("*script*")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        # Should find 2 conversations with "script" (id2 and id3)
        if "Found 2 conversation(s)" in output:
            print("SUCCESS: Wildcard search found conversations")
        else:
            print("FAILED: Wildcard search did not work properly")
            return False
        
        # Test 3: Starting wildcard "py*"
        print("\nTest 3: Starting wildcard search 'py*'")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("py*")
        output = f.getvalue()
        
        # Should find conversations that start with "py" (case-insensitive)
        if "Found" in output and "conversation(s)" in output:
            print("SUCCESS: Starting wildcard search works")
        else:
            print("FAILED: Starting wildcard search did not work")
            return False
        
        # Test 4: Search for non-existent term
        print("\nTest 4: Search for non-existent term 'xyz123'")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("xyz123")
        output = f.getvalue()
        
        if "No conversations found" in output:
            print("SUCCESS: Correctly handles non-existent search term")
        else:
            print("FAILED: Did not handle non-existent search term properly")
            return False
        
        print("\nAll comprehensive search tests passed!")
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_search_in_content():
    """Test search in user prompts and responses, not just subject."""
    print("\nTesting search in content (prompts/responses)...")
    
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
                if "machine learning" in prompt.lower():
                    return "Machine learning is a subset of AI that focuses on algorithms..."
                return f"Mock response to: {prompt}"
                
            def generate_subject(self, prompt, response):
                return f"Subject: {prompt[:20]}..."
        
        # Create conversation tree
        from conversation_tree import ConversationTree
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create a conversation with "machine learning" in the prompt
        id1 = conversation_tree.create_conversation("How does machine learning work?", None, None)
        print(f"Created conversation with ID: {id1}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Search for "learning" which should match in the prompt
        print("Searching for 'learning' in prompt content...")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("learning")
        output = f.getvalue()
        
        if "Found 1 conversation(s)" in output:
            print("SUCCESS: Found conversation by searching in prompt content")
        else:
            print("FAILED: Did not find conversation by searching in prompt content")
            print(f"Output: {repr(output)}")
            return False
        
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    print("Running comprehensive tests for 'search' command functionality...\n")
    
    success1 = test_search_comprehensive()
    success2 = test_search_in_content()
    
    if success1 and success2:
        print("\nAll comprehensive tests for 'search' command passed!")
    else:
        print("\nSome comprehensive tests for 'search' command failed!")
        sys.exit(1)