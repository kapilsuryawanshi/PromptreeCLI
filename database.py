import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple

class DatabaseManager:
    """Manages SQLite database operations for the Promptree application."""
    
    def __init__(self, db_path: str = None):
        """Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default in home directory.
        """
        if db_path is None:
            home_dir = os.path.expanduser("~")
            self.db_path = os.path.join(home_dir, "promptree.db")
        else:
            self.db_path = db_path
        
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                model_name TEXT NOT NULL,
                user_prompt TEXT NOT NULL,
                llm_response TEXT,
                pid INTEGER,
                user_prompt_timestamp DATETIME NOT NULL,
                llm_response_timestamp DATETIME,
                FOREIGN KEY (pid) REFERENCES conversations (id)
            )
        ''')
        
        # Create index on pid for faster tree traversal
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pid ON conversations(pid)')
        
        conn.commit()
        conn.close()
    
    def add_conversation(self, subject: str, model_name: str, user_prompt: str, 
                        llm_response: str = None, pid: int = None,
                        user_prompt_timestamp: datetime = None, 
                        llm_response_timestamp: datetime = None) -> int:
        """Add a new conversation to the database.
        
        Args:
            subject: Subject of the conversation
            model_name: Name of the LLM model used
            user_prompt: User's prompt text
            llm_response: LLM's response text (optional)
            pid: Parent conversation ID (optional, None for root node)
            user_prompt_timestamp: Timestamp of user prompt (optional, defaults to now)
            llm_response_timestamp: Timestamp of LLM response (optional)
            
        Returns:
            ID of the newly created conversation
        """
        if user_prompt_timestamp is None:
            user_prompt_timestamp = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations 
            (subject, model_name, user_prompt, llm_response, pid, user_prompt_timestamp, llm_response_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (subject, model_name, user_prompt, llm_response, pid, user_prompt_timestamp, llm_response_timestamp))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return new_id
    
    def get_conversation(self, conv_id: int) -> Optional[Tuple]:
        """Get a conversation by its ID.
        
        Args:
            conv_id: ID of the conversation to retrieve
            
        Returns:
            Conversation tuple (id, subject, model_name, user_prompt, llm_response, 
                               pid, user_prompt_timestamp, llm_response_timestamp) or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, subject, model_name, user_prompt, llm_response, 
                   pid, user_prompt_timestamp, llm_response_timestamp
            FROM conversations WHERE id = ?
        ''', (conv_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def get_conversation_chain(self, conv_id: int) -> List[Tuple]:
        """Get the conversation chain from root to the given conversation ID.
        
        Args:
            conv_id: ID of the conversation to trace back from
            
        Returns:
            List of conversations from root to the given conversation ID, ordered from root to leaf
        """
        chain = []
        current_id = conv_id
        
        while current_id is not None:
            conversation = self.get_conversation(current_id)
            if conversation is None:
                break
            
            chain.insert(0, conversation)  # Insert at beginning to maintain order
            current_id = conversation[5]  # pid is at index 5
        
        return chain
    
    def get_root_conversations(self) -> List[Tuple]:
        """Get all root conversations (those without a parent).
        
        Returns:
            List of root conversations ordered by timestamp (most recent first)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, subject, model_name, user_prompt, llm_response, 
                   pid, user_prompt_timestamp, llm_response_timestamp
            FROM conversations
            WHERE pid IS NULL
            ORDER BY user_prompt_timestamp DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_child_conversations(self, parent_id: int) -> List[Tuple]:
        """Get all child conversations of a given parent.
        
        Args:
            parent_id: ID of the parent conversation
            
        Returns:
            List of child conversations ordered by timestamp
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, subject, model_name, user_prompt, llm_response, 
                   pid, user_prompt_timestamp, llm_response_timestamp
            FROM conversations
            WHERE pid = ?
            ORDER BY user_prompt_timestamp ASC
        ''', (parent_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_descendant_conversations(self, parent_id: int) -> List[Tuple]:
        """Get all descendant conversations of a given parent (recursive).
        
        Args:
            parent_id: ID of the parent conversation
            
        Returns:
            List of all descendant conversations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recursive CTE to get all descendants
        cursor.execute('''
            WITH RECURSIVE descendants AS (
                SELECT id, subject, model_name, user_prompt, llm_response, 
                       pid, user_prompt_timestamp, llm_response_timestamp
                FROM conversations
                WHERE pid = ?
                UNION ALL
                SELECT c.id, c.subject, c.model_name, c.user_prompt, c.llm_response, 
                       c.pid, c.user_prompt_timestamp, c.llm_response_timestamp
                FROM conversations c
                JOIN descendants d ON c.pid = d.id
            )
            SELECT id, subject, model_name, user_prompt, llm_response, 
                   pid, user_prompt_timestamp, llm_response_timestamp
            FROM descendants
        ''', (parent_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def update_subject(self, conv_id: int, new_subject: str):
        """Update the subject of a conversation.
        
        Args:
            conv_id: ID of the conversation to update
            new_subject: New subject text
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE conversations
            SET subject = ?
            WHERE id = ?
        ''', (new_subject, conv_id))
        
        conn.commit()
        conn.close()
    
    def update_conversation_parent(self, conv_id: int, new_parent_id: Optional[int]):
        """Update the parent of a conversation.
        
        Args:
            conv_id: ID of the conversation to update
            new_parent_id: New parent ID (None for root conversation)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE conversations
            SET pid = ?
            WHERE id = ?
        ''', (new_parent_id, conv_id))
        
        conn.commit()
        conn.close()
    
    def delete_conversation(self, conv_id: int):
        """Delete a conversation and all its descendants.
        
        Args:
            conv_id: ID of the conversation to delete
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Use recursive CTE to delete all descendants
        cursor.execute('''
            WITH RECURSIVE descendants AS (
                SELECT id
                FROM conversations
                WHERE id = ?
                UNION ALL
                SELECT c.id
                FROM conversations c
                JOIN descendants d ON c.pid = d.id
            )
            DELETE FROM conversations
            WHERE id IN descendants
        ''', (conv_id,))
        
        conn.commit()
        conn.close()
    
    def get_conversation_tree(self, root_id: int) -> dict:
        """Get the conversation tree starting from a root.
        
        Args:
            root_id: ID of the root conversation
            
        Returns:
            Dictionary representing the tree structure
        """
        root_conversation = self.get_conversation(root_id)
        if not root_conversation:
            return None
        
        tree = {
            'id': root_conversation[0],
            'subject': root_conversation[1],
            'model_name': root_conversation[2],
            'user_prompt': root_conversation[3],
            'llm_response': root_conversation[4],
            'pid': root_conversation[5],
            'user_prompt_timestamp': root_conversation[6],
            'llm_response_timestamp': root_conversation[7],
            'children': []
        }
        
        # Get direct children
        children = self.get_child_conversations(root_id)
        for child in children:
            child_tree = self.get_conversation_tree(child[0])  # child[0] is the id
            if child_tree:
                tree['children'].append(child_tree)
        
        return tree

    def search_conversations(self, search_term: str) -> List[Tuple]:
        """Search for conversations containing the given term in subject, user_prompt, or llm_response.
        
        Args:
            search_term: Term to search for (supports % wildcards, case-insensitive)
            
        Returns:
            List of conversations matching the search term
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Search in subject, user_prompt, and llm_response fields (case-insensitive)
        cursor.execute('''
            SELECT id, subject, model_name, user_prompt, llm_response, 
                   pid, user_prompt_timestamp, llm_response_timestamp
            FROM conversations
            WHERE LOWER(subject) LIKE LOWER(?)
               OR LOWER(user_prompt) LIKE LOWER(?)
               OR (llm_response IS NOT NULL AND LOWER(llm_response) LIKE LOWER(?))
            ORDER BY user_prompt_timestamp DESC
        ''', (search_term, search_term, search_term))

        results = cursor.fetchall()
        conn.close()

        return results