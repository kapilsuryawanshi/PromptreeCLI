#!/usr/bin/env python
"""
Test script to verify the linked conversations editing functionality
"""
import tempfile
import os
import sys

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DatabaseManager
import utils

def test_linked_conversations_editing():
    # Create a database manager
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db_manager = DatabaseManager(db_path=temp_db_path)
        
        # Create a main conversation
        conv_id = db_manager.add_conversation(
            subject="Main Conversation",
            model_name="test-model",
            user_prompt="Main user prompt",
            llm_response="Main LLM response"
        )
        print(f"Created main conversation with ID: {conv_id}")
        
        # Create two other conversations to link to
        conv2_id = db_manager.add_conversation(
            subject="Linked Conversation 1",
            model_name="test-model", 
            user_prompt="Linked prompt 1",
            llm_response="Linked response 1"
        )
        print(f"Created linked conversation 1 with ID: {conv2_id}")
        
        conv3_id = db_manager.add_conversation(
            subject="Linked Conversation 2",
            model_name="test-model", 
            user_prompt="Linked prompt 2",
            llm_response="Linked response 2"
        )
        print(f"Created linked conversation 2 with ID: {conv3_id}")
        
        # Create a text file content with updated linked IDs
        # Get the original conversation
        conversation = db_manager.get_conversation(conv_id)
        
        # Generate the text format
        text_content = utils.conversation_to_text(conversation, db_manager)
        print(f"Original text content:\n{text_content}")
        
        # Modify the text content to update linked conversations
        # Change LINKED_CONVERSATIONS_ID to include both conv2_id and conv3_id
        modified_text = text_content.replace(
            f"LINKED_CONVERSATIONS_ID: ",
            f"LINKED_CONVERSATIONS_ID: {conv2_id},{conv3_id}"
        )
        print(f"Modified text content:\n{modified_text}")
        
        # Parse the modified text
        updated_data = utils.parse_conversation_text(modified_text)
        print(f"Parsed data: {updated_data}")
        
        # Verify the linked IDs were parsed correctly
        expected_linked_ids = {conv2_id, conv3_id}
        parsed_linked_ids = set(updated_data['linked_ids'])
        
        assert expected_linked_ids == parsed_linked_ids, f"Expected {expected_linked_ids}, got {parsed_linked_ids}"
        
        print("Linked conversations editing test passed!")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_linked_conversations_editing()