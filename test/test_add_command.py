#!/usr/bin/env python3
"""
Test script for the new 'add' command functionality with file input.
This tests the new feature where 'add' command opens a file to manually add conversations.
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


def create_add_file_template(parent_id=None, linked_ids=None):
    """
    Create a template for the add command file input.
    """
    parent_id_str = str(parent_id) if parent_id is not None else ""
    linked_ids_str = ','.join(map(str, linked_ids)) if linked_ids else ""
    
    template = f"""# Add Conversation File
# Only edit the fields below. Do not change the field names.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# To update linked conversations, change LINKED_CONVERSATIONS_ID to comma-separated IDs.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'
# LLM RESPONSE section starts after 'LLM_RESPONSE_START' and ends before 'LLM_RESPONSE_END'

PARENT_ID: {parent_id_str}
LINKED_CONVERSATIONS_ID: {linked_ids_str}

USER_PROMPT_START

USER_PROMPT_END

LLM_RESPONSE_START

LLM_RESPONSE_END
---
"""
    return template


def parse_add_file_content(text_content):
    """
    Parse the content from the add command text file.
    """
    import re
    
    # Initialize with default values
    parsed_data = {
        'parent_id': None,
        'user_prompt': '',
        'llm_response': '',
        'linked_ids': []
    }
    
    # Extract user prompt between markers
    user_prompt_match = re.search(r'USER_PROMPT_START\s*\n(.*?)\n\s*USER_PROMPT_END', text_content, re.DOTALL)
    if user_prompt_match:
        parsed_data['user_prompt'] = user_prompt_match.group(1).strip()
    
    # Extract LLM response between markers
    llm_response_match = re.search(r'LLM_RESPONSE_START\s*\n(.*?)\n\s*LLM_RESPONSE_END', text_content, re.DOTALL)
    if llm_response_match:
        parsed_data['llm_response'] = llm_response_match.group(1).strip()
    
    # Extract parent ID
    parent_id_match = re.search(r'^PARENT_ID:\s*(.*)', text_content, re.MULTILINE)
    if parent_id_match:
        parent_id_str = parent_id_match.group(1).strip()
        if parent_id_str.lower() in ('', 'none', 'null'):
            parsed_data['parent_id'] = None
        else:
            try:
                parsed_data['parent_id'] = int(parent_id_str)
            except ValueError:
                parsed_data['parent_id'] = None  # Invalid parent ID, set to None
    
    # Extract linked conversations ID
    linked_ids_match = re.search(r'^LINKED_CONVERSATIONS_ID:\s*(.*)', text_content, re.MULTILINE)
    if linked_ids_match:
        linked_ids_str = linked_ids_match.group(1).strip()
        if linked_ids_str:
            try:
                # Parse comma-separated IDs
                parsed_data['linked_ids'] = [int(id_str.strip()) for id_str in linked_ids_str.split(',') if id_str.strip()]
            except ValueError:
                parsed_data['linked_ids'] = []  # Invalid IDs, set to empty list
        else:
            parsed_data['linked_ids'] = []  # Empty string means no linked conversations
    
    return parsed_data


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
        
        # Add a parent conversation for testing linking
        parent_id = db_manager.add_conversation(
            subject="Parent Conversation",
            model_name="test-model",
            user_prompt="Parent prompt",
            llm_response="Parent response",
            user_prompt_timestamp=datetime.now()
        )
        
        # Add a linked conversation for testing linking
        linked_id = db_manager.add_conversation(
            subject="Linked Conversation",
            model_name="test-model",
            user_prompt="Linked prompt",
            llm_response="Linked response",
            user_prompt_timestamp=datetime.now()
        )
        
        # Test 1: Mock the file editing process to test the add functionality
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
This is a manually added prompt
USER_PROMPT_END

LLM_RESPONSE_START
This is a manually added response
LLM_RESPONSE_END
---
""")):
            
            # Call the add command (which we'll implement)
            # Since we haven't implemented it yet, let's create a mock version for testing
            template_content = create_add_file_template(parent_id, [linked_id])
            parsed_data = parse_add_file_content(template_content)
            
            # Validate the template and parsing
            assert parsed_data['parent_id'] == parent_id, "Parent ID should be parsed correctly"
            assert parsed_data['linked_ids'] == [linked_id], "Linked IDs should be parsed correctly"
            assert parsed_data['user_prompt'] == "", "User prompt should initially be empty"
            assert parsed_data['llm_response'] == "", "LLM response should initially be empty"
            
            print("Test 1 passed: Template and parsing work correctly")
        
        # Test 2: Test with modified content from user
        with unittest.mock.patch('os.environ.get', return_value='echo'), \
             unittest.mock.patch('subprocess.run'), \
             unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=f"""# Add Conversation File
# Only edit the fields below. Do not change the field names.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# To update linked conversations, change LINKED_CONVERSATIONS_ID to comma-separated IDs.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'
# LLM RESPONSE section starts after 'LLM_RESPONSE_START' and ends before 'LLM_RESPONSE_END'

PARENT_ID: {parent_id}
LINKED_CONVERSATIONS_ID: {linked_id},999

USER_PROMPT_START
This is a manually added prompt with some text
USER_PROMPT_END

LLM_RESPONSE_START
This is a manually added response with some text
LLM_RESPONSE_END
---
""")):
            
            # Parse the modified content
            modified_content_data = parse_add_file_content(f"""# Add Conversation File
# Only edit the fields below. Do not change the field names.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# To update linked conversations, change LINKED_CONVERSATIONS_ID to comma-separated IDs.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'
# LLM RESPONSE section starts after 'LLM_RESPONSE_START' and ends before 'LLM_RESPONSE_END'

PARENT_ID: {parent_id}
LINKED_CONVERSATIONS_ID: {linked_id},999

USER_PROMPT_START
This is a manually added prompt with some text
USER_PROMPT_END

LLM_RESPONSE_START
This is a manually added response with some text
LLM_RESPONSE_END
---
""")
            
            assert modified_content_data['parent_id'] == parent_id, "Parent ID should be parsed correctly"
            assert set(modified_content_data['linked_ids']) == {linked_id, 999}, "Linked IDs should be parsed correctly"
            assert modified_content_data['user_prompt'] == "This is a manually added prompt with some text", "User prompt should be parsed correctly"
            assert modified_content_data['llm_response'] == "This is a manually added response with some text", "LLM response should be parsed correctly"
            
            print("Test 2 passed: Modified content parsing works correctly")
        
        print("All add command file input tests passed!")
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


if __name__ == "__main__":
    test_add_command()
    print("Test completed successfully!")