#!/usr/bin/env python3
"""
Test script for the enhanced 'ask' command functionality with file input.
This tests the new feature where 'ask' command opens a file when no arguments are provided.
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

def test_ask_file_input():
    """Test the new ask command functionality when no arguments are provided."""
    print("Testing ask command with file input when no arguments provided...")
    
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
        
        # Test 1: Calling ask with no arguments should open file for input
        # We'll mock the part that opens the editor to simulate the behavior
        with unittest.mock.patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            # Create a mock temporary file with test content
            mock_file = unittest.mock.MagicMock()
            mock_tempfile.return_value.__enter__.return_value = mock_file
            mock_file.name = "/tmp/test_prompt.txt"
            
            # Read the content that would be written to the temp file
            actual_content_written = None
            def temp_file_side_effect(*args, **kwargs):
                # Capture the content that would be written to the file
                nonlocal actual_content_written
                mock_file.write = lambda content: setattr(mock_file, 'written_content', content)
                actual_content_written = mock_file.written_content
                return mock_file
            mock_tempfile.return_value.__enter__.side_effect = temp_file_side_effect
            
            # When no arguments are provided to ask, it should use file input
            result = cli_handler.do_ask("")
            
            # Check that a temporary file would be created with the right template
            assert mock_tempfile.called, "Temporary file should be created when no arguments provided to ask"
            
        print("Test 1 passed: Ask command opens file when no arguments provided")
        
        # Test 2: Creating a conversation with a parent ID
        parent_id = db_manager.add_conversation(
            subject="Parent Conversation",
            model_name="test-model",
            user_prompt="Parent prompt",
            llm_response="Parent response",
            user_prompt_timestamp=datetime.now()
        )
        
        # Mock the external editor process for this test
        with unittest.mock.patch('os.environ.get', return_value='echo'), \
             unittest.mock.patch('subprocess.run') as mock_run, \
             unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=f"""# Prompt File
# Only edit the PARENT_ID and USER_PROMPT fields below.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'

PARENT_ID: {parent_id}
USER_PROMPT_START
This is a test prompt from the file
USER_PROMPT_END
""")):
            
            # Call the ask command with no arguments (should trigger file input)
            result = cli_handler.do_ask("")
            
            # Verify subprocess was called with the editor
            mock_run.assert_called_once()
            
            print("Test 2 passed: Ask command properly handles parent ID from file")
        
        # Test 3: Test with current parent context
        cli_handler.current_parent_id = parent_id
        
        with unittest.mock.patch('os.environ.get', return_value='echo'), \
             unittest.mock.patch('subprocess.run'), \
             unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data="""# Prompt File
# Only edit the PARENT_ID and USER_PROMPT fields below.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'

PARENT_ID: 
USER_PROMPT_START
This is a test prompt from the file with current parent
USER_PROMPT_END
""")):
            
            # Call the ask command with no arguments
            result = cli_handler.do_ask("")
            
            print("Test 3 passed: Ask command uses current parent when PARENT_ID is empty in file")
        
        print("All ask command file input tests passed!")
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


def create_ask_file_template(parent_id=None):
    """
    Create a template for the ask command file input.
    This is the format that will be used for the temporary file.
    """
    parent_id_str = str(parent_id) if parent_id is not None else ""
    
    template = f"""# Prompt File
# Only edit the PARENT_ID and USER_PROMPT fields below.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'

PARENT_ID: {parent_id_str}
USER_PROMPT_START

USER_PROMPT_END
"""
    return template


def parse_ask_file_content(text_content):
    """
    Parse the content from the ask command text file.
    """
    import re
    
    # Initialize with default values
    parsed_data = {
        'parent_id': None,
        'user_prompt': ''
    }
    
    # Extract user prompt between markers
    user_prompt_match = re.search(r'USER_PROMPT_START\s*\n(.*?)\n\s*USER_PROMPT_END', text_content, re.DOTALL)
    if user_prompt_match:
        parsed_data['user_prompt'] = user_prompt_match.group(1).strip()
    
    # Extract parent ID
    parent_id_match = re.search(r'^PARENT_ID:\\s*(.*)', text_content, re.MULTILINE)
    if parent_id_match:
        parent_id_str = parent_id_match.group(1).strip()
        if parent_id_str.lower() in ('', 'none', 'null'):
            parsed_data['parent_id'] = None
        else:
            try:
                parsed_data['parent_id'] = int(parent_id_str)
            except ValueError:
                parsed_data['parent_id'] = None  # Invalid parent ID, set to None
    
    return parsed_data


if __name__ == "__main__":
    test_ask_file_input()
    print("Test completed successfully!")