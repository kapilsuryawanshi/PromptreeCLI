#!/usr/bin/env python
"""
Test script to verify link functionality implementation
"""
import os
import sys
import sqlite3

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DatabaseManager

def test_links_functionality():
    # Create a test database
    test_db_path = 'test_links.db'
    
    # Initialize database manager
    db_manager = DatabaseManager(db_path=test_db_path)
    
    # Verify the conversation_links table was created
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Check if conversation_links table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_links';")
    table_exists = cursor.fetchone() is not None
    print(f"conversation_links table exists: {table_exists}")
    
    if table_exists:
        # Get table schema
        cursor.execute("PRAGMA table_info(conversation_links);")
        schema = cursor.fetchall()
        print("Table schema:")
        for col in schema:
            print(f"  {col}")
        
        # Create some test conversations
        conv1_id = db_manager.add_conversation(
            subject="Test Conversation 1",
            model_name="test-model",
            user_prompt="Test prompt 1",
            llm_response="Test response 1"
        )
        print(f"Created conversation 1 with ID: {conv1_id}")
        
        conv2_id = db_manager.add_conversation(
            subject="Test Conversation 2",
            model_name="test-model",
            user_prompt="Test prompt 2",
            llm_response="Test response 2"
        )
        print(f"Created conversation 2 with ID: {conv2_id}")
        
        conv3_id = db_manager.add_conversation(
            subject="Test Conversation 3",
            model_name="test-model",
            user_prompt="Test prompt 3",
            llm_response="Test response 3"
        )
        print(f"Created conversation 3 with ID: {conv3_id}")
        
        # Test adding a link between conversations
        try:
            db_manager.add_conversation_link(conv1_id, conv2_id)
            print(f"Successfully linked conversation {conv1_id} to {conv2_id}")
        except Exception as e:
            print(f"Error adding link: {e}")
        
        # Test getting linked conversations
        linked = db_manager.get_linked_conversations(conv1_id)
        print(f"Conversations linked to {conv1_id}: {len(linked)} found")
        for conv in linked:
            print(f"  - ID: {conv[0]}, Subject: {conv[1]}")
        
        # Test getting link IDs
        link_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Link IDs for conversation {conv1_id}: {link_ids}")
        
        # Test removing a link
        try:
            db_manager.remove_conversation_link(conv1_id, conv2_id)
            print(f"Successfully removed link between {conv1_id} and {conv2_id}")
            
            # Verify the link was removed
            linked_after = db_manager.get_linked_conversations(conv1_id)
            print(f"Conversations linked to {conv1_id} after removal: {len(linked_after)} found")
        except Exception as e:
            print(f"Error removing link: {e}")
        
        # Test adding multiple links (bidirectional)
        try:
            db_manager.add_conversation_link(conv1_id, conv2_id)
            db_manager.add_conversation_link(conv1_id, conv3_id)
            print(f"Successfully added multiple links for conversation {conv1_id}")
            
            # Check all links for conv1
            link_ids = db_manager.get_conversation_link_ids(conv1_id)
            print(f"All link IDs for conversation {conv1_id}: {link_ids}")
            
            # Check all links for conv2 (should include conv1)
            link_ids_2 = db_manager.get_conversation_link_ids(conv2_id)
            print(f"All link IDs for conversation {conv2_id}: {link_ids_2}")
        except Exception as e:
            print(f"Error adding multiple links: {e}")
        
        # Test removing all links
        try:
            db_manager.remove_all_conversation_links(conv1_id)
            print(f"Successfully removed all links for conversation {conv1_id}")
            
            link_ids = db_manager.get_conversation_link_ids(conv1_id)
            print(f"Link IDs for conversation {conv1_id} after removing all: {link_ids}")
        except Exception as e:
            print(f"Error removing all links: {e}")
    
    # Clean up
    conn.close()
    os.remove(test_db_path)
    print("Test completed successfully!")

if __name__ == "__main__":
    test_links_functionality()