#!/usr/bin/env python3
"""
Test script for the new 'add' command functionality with file input.
"""

import os
import sys
import tempfile
from datetime import datetime
import unittest.mock

# Add the parent directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from database import DatabaseManager
from cli import CLIHandler


def test_add_command():
    """Test the new add command functionality."""
    print("Testing add command with file input...")
    
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
                if stream_callback:
                    response = f"Mock response to: {prompt}"
                    stream_callback(response)
                    return response
                return f"Mock response to: {prompt}"
                
            def generate_subject(self, prompt, response):
                return f"Subject for: {prompt[:30]}..."
        
        # Create mock conversation tree
        class MockConversationTree:
            def __init__(self, db_manager, ollama_client):
                self.db_manager = db_manager
                self.ollama_client = ollama_client
            
            def create_conversation(self, prompt, parent_id, stream_callback):
                # Simulate creating a conversation and return an ID
                subject = self.ollama_client.generate_subject(prompt, f"Mock response to: {prompt}")
                return self.db_manager.add_conversation(
                    subject=subject,
                    model_name=self.ollama_client.model_name,
                    user_prompt=prompt,
                    llm_response=f"Mock response to: {prompt}",
                    pid=parent_id,
                    user_prompt_timestamp=datetime.now()
                )
        
        ollama_client = MockOllamaClient("test-model")
        conversation_tree = MockConversationTree(db_manager, ollama_client)
        cli_handler = CLIHandler(db_manager, conversation_tree, "test-model")
        
        # Add a parent conversation for testing
        parent_id = db_manager.add_conversation(
            subject="Parent Conversation",
            model_name="test-model",
            user_prompt="Parent prompt",
            llm_response="Parent response",
            user_prompt_timestamp=datetime.now()
        )
        
        # Add a linked conversation for testing
        linked_id = db_manager.add_conversation(
            subject="Linked Conversation",
            model_name="test-model",
            user_prompt="Linked prompt",
            llm_response="Linked response",
            user_prompt_timestamp=datetime.now()
        )
        
        # Test the new add functionality
        with unittest.mock.patch('os.environ.get', return_value='echo'), \
             unittest.mock.patch('subprocess.run'), \
             unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=f"""# Add Conversation File
# Only edit the fields below. Do not change the field names.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# To update linked conversations, change LINKED_CONVERSATIONS_ID to comma-separated IDs.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'
# LLM RESPONSE section starts after 'LLM_RESPONSE_START' and ends before 'LLM_RESPONSE_END'

PARENT_ID: {parent_id}
LINKED_CONVERSATIONS_ID: {linked_id}

USER_PROMPT_START
This is a manually added prompt with some text
USER_PROMPT_END

LLM_RESPONSE_START
This is a manually added response with some text
LLM_RESPONSE_END
---
""")):
            
            # Call the add command (which should now exist)
            # Check if the method exists
            assert hasattr(cli_handler, 'do_add'), "do_add method should exist"
            print("PASS: do_add method exists")
            
            # Call the do_add method to test the functionality
            cli_handler.do_add("")
            
            # Verify the conversation was added to the database
            all_conversations = db_manager.get_root_conversations()
            # Since the new conversation has a parent, it won't show up in root conversations
            # But we can get it directly by ID or by querying children of parent
            all_conv_ids = [conv[0] for conv in db_manager.get_child_conversations(parent_id)]
            assert len(all_conv_ids) == 1, "A new conversation should have been added as a child of the parent"
            
            new_conv_id = all_conv_ids[0]
            new_conversation = db_manager.get_conversation(new_conv_id)
            assert new_conversation is not None, "New conversation should exist in database"
            
            # Verify the details
            assert new_conversation[1] == "Subject for: This is a manually added promp...", "Subject should be generated correctly"
            assert new_conversation[3] == "This is a manually added prompt with some text", "User prompt should match"
            assert new_conversation[4] == "This is a manually added response with some text", "LLM response should match"
            assert new_conversation[5] == parent_id, "Parent ID should be set correctly"
            
            # Verify the link was created
            linked_convs = db_manager.get_conversation_link_ids(new_conv_id)
            assert linked_id in linked_convs, "Link to the specified conversation should be created"
            
            print(f"PASS: New conversation {new_conv_id} was added with correct values")
        
        print("All add command tests passed!")
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


if __name__ == "__main__":
    test_add_command()
    print("Test completed successfully!")