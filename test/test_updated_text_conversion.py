#!/usr/bin/env python
"""
Test script to verify the updated plain text conversion functionality for conversation editing
"""
import tempfile
import os
import sys

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DatabaseManager
import utils

def test_updated_text_conversion():
    # Create a database manager
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db_manager = DatabaseManager(db_path=temp_db_path)
        
        # Create a test conversation
        conv_id = db_manager.add_conversation(
            subject="Test Subject",
            model_name="test-model",
            user_prompt="Test user prompt",
            llm_response="Test LLM response"
        )
        print(f"Created conversation with ID: {conv_id}")
        
        # Link with another conversation to test linked conversations display
        conv2_id = db_manager.add_conversation(
            subject="Linked Conversation",
            model_name="test-model", 
            user_prompt="Linked prompt",
            llm_response="Linked response"
        )
        print(f"Created linked conversation with ID: {conv2_id}")
        
        # Link the conversations
        db_manager.add_conversation_link(conv_id, conv2_id)
        print(f"Linked conversation {conv_id} to {conv2_id}")
        
        # Get the conversation
        conversation = db_manager.get_conversation(conv_id)
        print(f"Original conversation: {conversation}")
        
        # Test conversion to plain text with db manager
        text_content = utils.conversation_to_text(conversation, db_manager)
        print(f"Text content:\n{text_content}")
        
        # Test parsing text back (should only parse editable fields)
        updated_data = utils.parse_conversation_text(text_content)
        print(f"Parsed data: {updated_data}")
        
        # Verify that the conversion and parsing worked correctly for editable fields
        assert updated_data['subject'] == "Test Subject"
        assert updated_data['user_prompt'] == "Test user prompt"
        assert updated_data['llm_response'] == "Test LLM response"
        
        # Verify that non-editable fields are handled appropriately
        # (These should not be in updated_data since they're not editable)
        assert 'CONVERSATION_ID' not in updated_data
        assert 'MODEL_NAME' not in updated_data
        assert 'CREATED_TIMESTAMP' not in updated_data
        assert 'RESPONSE_TIMESTAMP' not in updated_data
        
        print("Updated plain text conversion and parsing test passed!")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_updated_text_conversion()