# Utility functions for the Promptree CLI application
import sys
import os

# Initialize colorama for cross-platform colored output
try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama
    
    def format_subject(subject: str) -> str:
        """Format subject text with yellow color."""
        return f"{Fore.YELLOW}{subject}{Style.RESET_ALL}"

    def format_prompt(prompt: str) -> str:
        """Format prompt text with cyan color."""
        return f"{Fore.CYAN}{prompt}{Style.RESET_ALL}"

    def format_response(response: str) -> str:
        """Format response text with green color."""
        return f"{Fore.GREEN}{response}{Style.RESET_ALL}"

    def format_error(error: str) -> str:
        """Format error text with red color."""
        return f"{Fore.RED}{error}{Style.RESET_ALL}"

except ImportError:
    # If colorama is not available, provide simple fallback functions
    def format_subject(subject: str) -> str:
        """Format subject text (no color without colorama)."""
        return subject

    def format_prompt(prompt: str) -> str:
        """Format prompt text (no color without colorama)."""
        return prompt

    def format_response(response: str) -> str:
        """Format response text (no color without colorama)."""
        return response

    def format_error(error: str) -> str:
        """Format error text (no color without colorama)."""
        return error


def conversation_to_text(conversation: tuple, db_manager=None) -> str:
    """Convert a conversation tuple to a plain text format for editing.
    
    Args:
        conversation: A tuple representing a conversation from the database
        db_manager: Database manager to fetch linked conversations
        
    Returns:
        Plain text format of the conversation with only editable fields
    """
    if not conversation:
        return ""
    
    # Extract conversation data from tuple
    # (id, subject, model_name, user_prompt, llm_response, pid, user_prompt_timestamp, llm_response_timestamp)
    conv_id, subject, model_name, user_prompt, llm_response, pid, user_prompt_timestamp, llm_response_timestamp = conversation
    
    # Get linked conversation IDs if db_manager is provided
    linked_ids = []
    if db_manager:
        linked_ids = db_manager.get_conversation_link_ids(conv_id)
    
    # Create a plain text format that's easy to edit
    text_content = f"""# Conversation Edit File
# Only edit the fields below. Do not change the field names.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# To update linked conversations, change LINKED_CONVERSATIONS_ID to comma-separated IDs.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'
# LLM RESPONSE section starts after 'LLM_RESPONSE_START' and ends before 'LLM_RESPONSE_END'

SUBJECT: {subject}
PARENT_ID: {pid if pid is not None else ''}
LINKED_CONVERSATIONS_ID: {','.join(map(str, linked_ids)) if linked_ids else ''}

USER_PROMPT_START
{user_prompt}
USER_PROMPT_END

LLM_RESPONSE_START
{llm_response if llm_response else ''}
LLM_RESPONSE_END
---
"""
    
    return text_content


def parse_conversation_text(text_content: str) -> dict:
    """Parse plain text content back to conversation data.
    
    Args:
        text_content: Plain text format of the conversation
        
    Returns:
        Dictionary with updated conversation fields
    """
    import re
    
    # Initialize with default values (only editable fields)
    updated_data = {
        'subject': '',
        'user_prompt': '',
        'llm_response': '',
        'pid': None,
        'linked_ids': []  # This will store linked conversation IDs to update
    }
    
    # Split the content by lines
    lines = text_content.split('\n')
    
    # Find the USER_PROMPT_START and USER_PROMPT_END markers
    user_prompt_start_idx = None
    user_prompt_end_idx = None
    llm_response_start_idx = None
    llm_response_end_idx = None
    
    for i, line in enumerate(lines):
        if line.strip() == 'USER_PROMPT_START':
            user_prompt_start_idx = i
        elif line.strip() == 'USER_PROMPT_END':
            user_prompt_end_idx = i
        elif line.strip() == 'LLM_RESPONSE_START':
            llm_response_start_idx = i
        elif line.strip() == 'LLM_RESPONSE_END':
            llm_response_end_idx = i
    
    # Extract user prompt if markers were found
    if user_prompt_start_idx is not None and user_prompt_end_idx is not None:
        updated_data['user_prompt'] = '\n'.join(lines[user_prompt_start_idx + 1:user_prompt_end_idx]).strip()
        # Remove the end marker if it was accidentally included
        if updated_data['user_prompt'].endswith('# USER PROMPT END (do not change this line)'):
            updated_data['user_prompt'] = updated_data['user_prompt'][:-len('# USER PROMPT END (do not change this line)')].strip()
    
    # Extract LLM response if markers were found
    if llm_response_start_idx is not None and llm_response_end_idx is not None:
        updated_data['llm_response'] = '\n'.join(lines[llm_response_start_idx + 1:llm_response_end_idx]).strip()
        # Remove the end marker if it was accidentally included
        if updated_data['llm_response'].endswith('# LLM RESPONSE END (do not change this line)'):
            updated_data['llm_response'] = updated_data['llm_response'][:-len('# LLM RESPONSE END (do not change this line)')].strip()
    
    # Extract only editable fields using regex
    # SUBJECT
    subject_match = re.search(r'^SUBJECT:\s*(.*)', text_content, re.MULTILINE)
    if subject_match:
        updated_data['subject'] = subject_match.group(1).strip()
    
    # Note: MODEL_NAME is in the text file but should not be editable - so we don't parse it
    
    # PARENT_ID
    parent_id_match = re.search(r'^PARENT_ID:\s*(.*)', text_content, re.MULTILINE)
    if parent_id_match:
        parent_id_str = parent_id_match.group(1).strip()
        if parent_id_str.lower() in ('', 'none', 'null'):
            updated_data['pid'] = None
        else:
            try:
                updated_data['pid'] = int(parent_id_str)
            except ValueError:
                updated_data['pid'] = None  # Invalid parent ID, set to None
    
    # LINKED_CONVERSATIONS_ID
    linked_ids_match = re.search(r'^LINKED_CONVERSATIONS_ID:\s*(.*)', text_content, re.MULTILINE)
    if linked_ids_match:
        linked_ids_str = linked_ids_match.group(1).strip()
        if linked_ids_str:
            try:
                # Parse comma-separated IDs
                updated_data['linked_ids'] = [int(id_str.strip()) for id_str in linked_ids_str.split(',') if id_str.strip()]
            except ValueError:
                updated_data['linked_ids'] = []  # Invalid IDs, set to empty list
        else:
            updated_data['linked_ids'] = []  # Empty string means no linked conversations
    
    return updated_data