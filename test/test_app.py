#!/usr/bin/env python3
"""
Test script for the Promptree CLI application.
This script tests various components without requiring Ollama to be running.
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
from ollama_client import OllamaClient
from conversation_tree import ConversationTree
from cli import CLIHandler

def test_database():
    """Test database functionality."""
    print("Testing database functionality...")
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(temp_db_path)
        
        # Test adding a conversation
        conv_id = db_manager.add_conversation(
            subject="Test Subject",
            model_name="test-model",
            user_prompt="Test prompt",
            llm_response="Test response",
            user_prompt_timestamp=datetime.now()
        )
        print(f"Added conversation with ID: {conv_id}")
        
        # Test retrieving the conversation
        conversation = db_manager.get_conversation(conv_id)
        assert conversation is not None, "Failed to retrieve conversation"
        assert conversation[1] == "Test Subject", "Subject doesn't match"
        print("Retrieved conversation successfully")
        
        # Test getting root conversations
        roots = db_manager.get_root_conversations()
        assert len(roots) == 1, "Expected 1 root conversation"
        print("Root conversations retrieved successfully")
        
        # Test updating subject
        db_manager.update_subject(conv_id, "Updated Test Subject")
        updated_conv = db_manager.get_conversation(conv_id)
        assert updated_conv[1] == "Updated Test Subject", "Subject update failed"
        print("Subject updated successfully")
        
        print("Database tests passed!")
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_cli_construction():
    """Test that CLI components can be constructed."""
    print("\nTesting CLI construction...")
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db_manager = DatabaseManager(temp_db_path)
        # Mock Ollama client to avoid requiring Ollama service
        class MockOllamaClient:
            def __init__(self, model_name):
                self.model_name = model_name
            
            def generate_response(self, prompt, context=None):
                return f"Mock response to: {prompt}"
                
            def generate_subject(self, prompt, response):
                return f"Subject for: {prompt[:30]}..."
        
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = ConversationTree(db_manager, ollama_client)
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        print("CLI components constructed successfully!")
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def run_tests():
    """Run all tests."""
    print("Running Promptree CLI application tests...\n")
    
    test_database()
    test_cli_construction()
    
    print("\nAll tests passed! The application structure is working correctly.")
    print("Note: The Ollama API communication tests were skipped as they require a running Ollama service.")

if __name__ == "__main__":
    run_tests()