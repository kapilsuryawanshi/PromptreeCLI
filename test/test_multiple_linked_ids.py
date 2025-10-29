#!/usr/bin/env python
"""
Test script to specifically verify multiple comma-separated linked conversation IDs
"""
import tempfile
import os
import sys

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DatabaseManager
import utils

def test_multiple_linked_ids():
    # Create a database manager
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db_path = temp_db.name
    
    try:
        db_manager = DatabaseManager(db_path=temp_db_path)
        
        # Create a main conversation
        main_conv_id = db_manager.add_conversation(
            subject="Main Conversation",
            model_name="test-model",
            user_prompt="Main user prompt",
            llm_response="Main LLM response"
        )
        print(f"Created main conversation with ID: {main_conv_id}")
        
        # Create multiple conversations to link to
        linked_conv_ids = []
        for i in range(1, 6):  # Creating 5 linked conversations
            conv_id = db_manager.add_conversation(
                subject=f"Linked Conversation {i}",
                model_name="test-model", 
                user_prompt=f"Linked prompt {i}",
                llm_response=f"Linked response {i}"
            )
            linked_conv_ids.append(conv_id)
            print(f"Created linked conversation {i} with ID: {conv_id}")
        
        # Get the original conversation and generate text format
        conversation = db_manager.get_conversation(main_conv_id)
        text_content = utils.conversation_to_text(conversation, db_manager)
        print(f"Original text content:\n{text_content}")
        
        # Create a modified text content with multiple linked IDs
        # Format them as comma-separated list
        new_linked_ids_str = ','.join(map(str, linked_conv_ids))
        modified_text = text_content.replace(
            "LINKED_CONVERSATIONS_ID: ",
            f"LINKED_CONVERSATIONS_ID: {new_linked_ids_str}"
        )
        print(f"Modified text content (with multiple linked IDs):\n{modified_text}")
        
        # Parse the modified text
        updated_data = utils.parse_conversation_text(modified_text)
        print(f"Parsed linked IDs: {updated_data['linked_ids']}")
        
        # Verify the linked IDs were parsed correctly
        expected_linked_ids = set(linked_conv_ids)
        parsed_linked_ids = set(updated_data['linked_ids'])
        
        assert expected_linked_ids == parsed_linked_ids, f"Expected {expected_linked_ids}, got {parsed_linked_ids}"
        
        print(f"Successfully parsed {len(parsed_linked_ids)} linked conversation IDs: {sorted(parsed_linked_ids)}")
        print("Multiple linked conversations IDs test passed!")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_multiple_linked_ids()