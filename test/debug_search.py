#!/usr/bin/env python3
"""
Simple test to debug the search functionality
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def test_database_directly():
    """Test database search directly."""
    print("Testing database search directly...")
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name

    try:
        db_manager = DatabaseManager(temp_db_path)
        
        # Add test data
        id1 = db_manager.add_conversation(
            subject="Python Programming Tutorial",
            model_name="test-model",
            user_prompt="How do I learn Python programming?",
            llm_response="Python is a great programming language..."
        )
        
        # Test exact match (case-insensitive)
        print(f"Searching for '%python%' (should match 'Python')")
        results = db_manager.search_conversations("%python%")
        print(f"Results for '%python%': {len(results)} matches")
        for result in results:
            print(f"  - ID: {result[0]}, Subject: {result[1]}")
        
        print(f"Searching for 'python' (without wildcards, should still match 'Python')")
        results = db_manager.search_conversations("python")
        print(f"Results for 'python': {len(results)} matches")
        for result in results:
            print(f"  - ID: {result[0]}, Subject: {result[1]}")
        
        print(f"Searching for '%Python%' (with wildcards, upper case)")
        results = db_manager.search_conversations("%Python%")
        print(f"Results for '%Python%': {len(results)} matches")
        for result in results:
            print(f"  - ID: {result[0]}, Subject: {result[1]}")
        
        return True
        
    finally:
        # Clean up the temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_database_directly()