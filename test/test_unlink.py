#!/usr/bin/env python
"""
Test script to verify unlink functionality
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

class TestCLIHandler(CLIHandler):
    """A CLI handler for testing that doesn't enter an interactive loop."""
    
    def __init__(self, db_manager, conversation_tree, model_name):
        super().__init__(db_manager, conversation_tree, model_name)
    
    def start_cli(self):
        """Override to avoid the interactive loop."""
        pass

def test_unlink_functionality():
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Initialize components
        db_manager = DatabaseManager(db_path=temp_db_path)
        ollama_client = OllamaClient(model_name='test-model')  # This will be mocked
        conversation_tree = ConversationTree(db_manager, ollama_client)
        
        # Create CLI handler
        cli_handler = TestCLIHandler(db_manager, conversation_tree, 'test-model')
        
        # Create test conversations
        conv1_id = db_manager.add_conversation(
            subject="Main Conversation",
            model_name="test-model",
            user_prompt="Main question",
            llm_response="Main response"
        )
        print(f"Created main conversation with ID: {conv1_id}")
        
        conv2_id = db_manager.add_conversation(
            subject="Related Conversation 1",
            model_name="test-model",
            user_prompt="Related question 1",
            llm_response="Related response 1"
        )
        print(f"Created related conversation 1 with ID: {conv2_id}")
        
        conv3_id = db_manager.add_conversation(
            subject="Related Conversation 2",
            model_name="test-model",
            user_prompt="Related question 2",
            llm_response="Related response 2"
        )
        print(f"Created related conversation 2 with ID: {conv3_id}")
        
        conv4_id = db_manager.add_conversation(
            subject="Related Conversation 3",
            model_name="test-model",
            user_prompt="Related question 3",
            llm_response="Related response 3"
        )
        print(f"Created related conversation 3 with ID: {conv4_id}")
        
        # Link conv1 to conv2, conv3, and conv4
        db_manager.add_conversation_link(conv1_id, conv2_id)
        db_manager.add_conversation_link(conv1_id, conv3_id)
        db_manager.add_conversation_link(conv1_id, conv4_id)
        print(f"Linked conversation {conv1_id} to {conv2_id}, {conv3_id}, and {conv4_id}")
        
        # Verify all links exist
        link_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Initial link IDs for conversation {conv1_id}: {link_ids}")
        assert len(link_ids) == 3, f"Expected 3 links, got {len(link_ids)}"
        assert set(link_ids) == {conv2_id, conv3_id, conv4_id}, "Link IDs don't match expected"
        
        # Test unlinking specific conversations
        # First, let's simulate what the edit command would do for unlinking
        # We'll use the database manager directly to test the functionality
        
        # Unlink from conv2 and conv3 only
        db_manager.remove_conversation_link(conv1_id, conv2_id)
        db_manager.remove_conversation_link(conv2_id, conv1_id)  # Remove both directions
        db_manager.remove_conversation_link(conv1_id, conv3_id)
        db_manager.remove_conversation_link(conv3_id, conv1_id)  # Remove both directions
        
        # Verify only conv4 remains linked
        link_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Link IDs for conversation {conv1_id} after unlinking: {link_ids}")
        assert len(link_ids) == 1, f"Expected 1 link after unlinking, got {len(link_ids)}"
        assert link_ids[0] == conv4_id, f"Expected {conv4_id} to remain linked, got {link_ids[0]}"
        
        print("Unlinking test passed!")
        
        # Let's also manually test the logic that CLI uses for unlinking
        # Add back the links to test full CLI workflow
        db_manager.add_conversation_link(conv1_id, conv2_id)
        db_manager.add_conversation_link(conv1_id, conv3_id)
        link_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Link IDs for conversation {conv1_id} after re-adding links: {link_ids}")
        assert len(link_ids) == 3, f"Expected 3 links after re-adding, got {len(link_ids)}"
        
        # Simulate the CLI edit command with -unlink
        def simulate_unlink_command(conv_id, unlink_ids_list):
            """Simulate the CLI unlink logic"""
            changes_made = []
            for unlink_id in unlink_ids_list:
                # Prevent unlinking from itself
                if unlink_id == conv_id:
                    print(f"Cannot unlink conversation {conv_id} from itself.")
                    continue
                # Try to remove the link in both directions
                try:
                    db_manager.remove_conversation_link(conv_id, unlink_id)
                    # Also try removing the reverse link in case it exists
                    db_manager.remove_conversation_link(unlink_id, conv_id)
                    changes_made.append(f"Unlinked from conversation {unlink_id}")
                except Exception as e:
                    print(f"Error unlinking from conversation {unlink_id}: {e}")
            return changes_made
        
        # Test the simulated unlink command
        changes = simulate_unlink_command(conv1_id, [conv2_id, conv3_id])
        print(f"Changes made: {changes}")
        
        # Verify only conv4 remains linked
        link_ids = db_manager.get_conversation_link_ids(conv1_id)
        print(f"Final link IDs for conversation {conv1_id}: {link_ids}")
        assert len(link_ids) == 1, f"Expected 1 link at end, got {len(link_ids)}"
        assert link_ids[0] == conv4_id, f"Expected {conv4_id} to remain linked, got {link_ids[0]}"
        
        print("Full unlink functionality test passed!")
        
    finally:
        # Clean up the temp database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_unlink_functionality()