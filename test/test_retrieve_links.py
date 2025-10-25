#!/usr/bin/env python
"""
Simple test script to verify that linked conversations can be retrieved
"""
import tempfile
import os
import sys

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DatabaseManager
from conversation_tree import ConversationTree
from ollama_client import OllamaClient

def test_retrieve_linked_conversations():
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Initialize components
        db_manager = DatabaseManager(db_path=temp_db_path)
        ollama_client = OllamaClient(model_name='test-model')  # This will be mocked
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create some test conversations
        conv1_id = db_manager.add_conversation(
            subject="Main Conversation",
            model_name="test-model",
            user_prompt="What is the capital of France?",
            llm_response="The capital of France is Paris."
        )
        print(f"Created main conversation with ID: {conv1_id}")
        
        conv2_id = db_manager.add_conversation(
            subject="Related Geography Facts",
            model_name="test-model",
            user_prompt="Tell me about European capitals",
            llm_response="Paris is the capital of France, Berlin is the capital of Germany, etc."
        )
        print(f"Created related conversation with ID: {conv2_id}")
        
        conv3_id = db_manager.add_conversation(
            subject="French Culture",
            model_name="test-model",
            user_prompt="What are some French cultural aspects?",
            llm_response="French culture includes art, cuisine, fashion, and architecture."
        )
        print(f"Created French culture conversation with ID: {conv3_id}")
        
        # Link the main conversation to the other two
        db_manager.add_conversation_link(conv1_id, conv2_id)
        db_manager.add_conversation_link(conv1_id, conv3_id)
        print(f"Linked conversation {conv1_id} to {conv2_id} and {conv3_id}")
        
        # Test retrieving linked conversations
        linked_convs = db_manager.get_linked_conversations(conv1_id)
        print(f"Number of linked conversations for {conv1_id}: {len(linked_convs)}")
        
        for conv in linked_convs:
            conv_id, subject, _, _, _, _, timestamp, _ = conv
            print(f"  - ID: {conv_id}, Subject: {subject}, Created: {timestamp}")
        
        # Verify that both linked conversations are retrieved
        linked_ids = [conv[0] for conv in linked_convs]  # Extract IDs
        assert conv2_id in linked_ids, f"Linked conversation {conv2_id} not found"
        assert conv3_id in linked_ids, f"Linked conversation {conv3_id} not found"
        assert len(linked_ids) == 2, f"Expected 2 linked conversations, got {len(linked_ids)}"
        
        # Test retrieving link IDs specifically
        link_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Link IDs for conversation {conv1_id}: {link_ids}")
        
        assert conv2_id in link_ids, f"Link ID {conv2_id} not found in link IDs"
        assert conv3_id in link_ids, f"Link ID {conv3_id} not found in link IDs"
        assert len(link_ids) == 2, f"Expected 2 link IDs, got {len(link_ids)}"
        
        print("\nAll tests passed! Linked conversations are properly stored and retrieved.")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_retrieve_linked_conversations()