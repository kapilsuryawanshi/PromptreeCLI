#!/usr/bin/env python
"""
Test script to verify the external editor functionality for conversation editing
"""
import tempfile
import os
import sys

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DatabaseManager
from conversation_tree import ConversationTree
from ollama_client import OllamaClient
from cli import CLIHandler
import utils

def test_xml_conversion():
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
        
        # Get the conversation
        conversation = db_manager.get_conversation(conv_id)
        print(f"Original conversation: {conversation}")
        
        # Test conversion to XML
        xml_content = utils.conversation_to_xml(conversation)
        print(f"XML content:\n{xml_content}")
        
        # Test parsing XML back
        updated_data = utils.parse_conversation_xml(xml_content)
        print(f"Parsed data: {updated_data}")
        
        # Verify that the conversion and parsing worked correctly
        assert updated_data['subject'] == "Test Subject"
        assert updated_data['user_prompt'] == "Test user prompt"
        assert updated_data['llm_response'] == "Test LLM response"
        
        print("XML conversion and parsing test passed!")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_xml_conversion()