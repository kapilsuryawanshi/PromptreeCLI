#!/usr/bin/env python3
"""
Test to verify the new 'search' command functionality with wildcard support and case-insensitivity
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from cli import CLIHandler

def test_search_command():
    """Test the new search command functionality."""
    print("Testing 'search' command functionality...")
    
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
        
        # Create some test conversations
        id1 = conversation_tree.create_conversation("This is the first conversation about Python", None, None)
        id2 = conversation_tree.create_conversation("This is the second conversation about Java", None, None)
        id3 = conversation_tree.create_conversation("Another conversation about JavaScript and Python", None, None)
        
        print(f"Created conversations with IDs: {id1}, {id2}, {id3}")
        
        # Create CLI handler
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Mock stdout to capture print output
        import io
        from contextlib import redirect_stdout
        
        # Test 1: Search for "python" (should match 2 conversations - case insensitive)
        print("\nTest 1: Searching for 'python' (case-insensitive)")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("python")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        # Count how many times "python" appears in the results
        python_matches = output.lower().count("python")
        if python_matches >= 2:  # Should match at least in subjects of 2 conversations
            print("SUCCESS: Found 'python' in multiple conversations (case-insensitive)")
        else:
            print(f"FAILED: Expected 'python' in at least 2 conversations, found in {python_matches}")
            return False
        
        # Test 2: Search with wildcard "*script*" (should match JavaScript and potentially other script terms)
        print("\nTest 2: Searching with wildcard '*script*'")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("*script*")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        # Should find "JavaScript" in id3's subject
        if "JavaScript" in output or "javascript" in output.lower():
            print("SUCCESS: Wildcard search found 'JavaScript' in results")
        else:
            print("FAILED: Wildcard search did not find 'JavaScript' in results")
            return False
        
        # Test 3: Search for something that doesn't exist
        print("\nTest 3: Searching for 'xyz123' (should find nothing)")
        f = io.StringIO()
        with redirect_stdout(f):
            cli_handler.do_search("xyz123")
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        
        if "No conversations found" in output:
            print("SUCCESS: Correctly reports when no matches found")
        else:
            print("FAILED: Did not report 'No conversations found' for nonexistent search")
            return False
        
        print("\nAll basic tests passed!")
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_database_search_function():
    """Test the database search function directly."""
    print("\nTesting database search function directly...")
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name

    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Add some test data directly to database
        id1 = db_manager.add_conversation(
            subject="Python Programming Tutorial",
            model_name="test-model",
            user_prompt="How do I learn Python programming?",
            llm_response="Python is a great programming language..."
        )
        
        id2 = db_manager.add_conversation(
            subject="JavaScript Basics",
            model_name="test-model", 
            user_prompt="Explain JavaScript basics",
            llm_response="JavaScript is a versatile language for web development..."
        )
        
        id3 = db_manager.add_conversation(
            subject="Advanced Python Concepts",
            model_name="test-model",
            user_prompt="Explain advanced Python concepts",
            llm_response="Generators, decorators and other advanced Python features..."
        )
        
        print(f"Added test conversations with IDs: {id1}, {id2}, {id3}")
        
        # Test case-insensitive search
        results = db_manager.search_conversations("%python%")
        print(f"Found {len(results)} results for '%python%'")
        
        if len(results) >= 2:  # Should find at least Python in subjects of id1 and id3
            print("SUCCESS: Database search found case-insensitive matches")
        else:
            print(f"FAILED: Expected at least 2 matches, found {len(results)}")
            return False
        
        # Test wildcard search
        results = db_manager.search_conversations("%script%")
        print(f"Found {len(results)} results for '%script%'")
        
        if len(results) >= 1:  # Should find JavaScript in id2
            print("SUCCESS: Database wildcard search works")
        else:
            print(f"FAILED: Expected at least 1 match for wildcard, found {len(results)}")
            return False
        
        print("Database search function tests passed!")
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    print("Running tests for 'search' command functionality...\n")
    
    success1 = test_search_command()
    success2 = test_database_search_function()
    
    if success1 and success2:
        print("\nAll tests for 'search' command passed!")
    else:
        print("\nSome tests for 'search' command failed!")
        sys.exit(1)