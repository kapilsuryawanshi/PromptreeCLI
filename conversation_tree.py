from typing import List, Optional, Callable
from database import DatabaseManager
from ollama_client import OllamaClient
from datetime import datetime

class ConversationTree:
    """Manages the conversation tree structure and context building."""
    
    def __init__(self, db_manager: DatabaseManager, ollama_client: OllamaClient):
        """
        Initialize the conversation tree manager.
        
        Args:
            db_manager: Database manager instance
            ollama_client: Ollama client instance
        """
        self.db_manager = db_manager
        self.ollama_client = ollama_client
    
    def build_context_history(self, parent_id: int) -> str:
        """
        Build context history by combining all conversations from root to parent.
        
        Args:
            parent_id: ID of the parent conversation
            
        Returns:
            Formatted context history string
        """
        conversation_chain = self.db_manager.get_conversation_chain(parent_id)
        
        if not conversation_chain:
            return ""
        
        context_parts = []
        for conv in conversation_chain:
            _, subject, _, user_prompt, llm_response, _, prompt_timestamp, response_timestamp = conv
            
            context_parts.append(f"Subject: {subject}")
            context_parts.append(f"User Prompt (at {prompt_timestamp}): {user_prompt}")
            if llm_response:
                context_parts.append(f"LLM Response (at {response_timestamp}): {llm_response}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def create_conversation(self, prompt: str, parent_id: Optional[int] = None, stream_callback: Optional[Callable[[str], None]] = None) -> int:
        """
        Create a new conversation with the LLM.
        
        Args:
            prompt: User's prompt
            parent_id: Optional parent conversation ID
            stream_callback: Optional callback function to handle streaming response chunks
            
        Returns:
            ID of the newly created conversation
        """
        # Determine the model name from the parent conversation or use a default
        model_name = self.ollama_client.model_name
        
        # Build context if there's a parent
        context = None
        if parent_id:
            context = self.build_context_history(parent_id)
        
        user_prompt_timestamp=datetime.now()

        # Generate response from LLM with streaming
        response = self.ollama_client.generate_response(prompt, context, stream_callback)
        
        # Generate a subject for the conversation
        subject = self.ollama_client.generate_subject(prompt, response)
        
        # Add conversation to database
        conv_id = self.db_manager.add_conversation(
            subject=subject,
            model_name=model_name,
            user_prompt=prompt,
            llm_response=response,
            pid=parent_id,
            user_prompt_timestamp=user_prompt_timestamp,
            llm_response_timestamp=datetime.now()
        )
        
        return conv_id
    
    def get_conversation_path(self, conv_id: int) -> List[int]:
        """
        Get the path from root to the given conversation ID.
        
        Args:
            conv_id: ID of the conversation
            
        Returns:
            List of conversation IDs from root to the given conversation
        """
        path = []
        current_id = conv_id
        
        while current_id is not None:
            path.insert(0, current_id)  # Insert at beginning to maintain order
            conversation = self.db_manager.get_conversation(current_id)
            if conversation:
                current_id = conversation[5]  # pid is at index 5
            else:
                current_id = None
        
        return path