import cmd
import sys
import re
import sqlite3
from typing import Optional
from database import DatabaseManager
from conversation_tree import ConversationTree
import utils

class CLIHandler(cmd.Cmd):
    """Command-line interface handler for the Promptree application."""
    
    def __init__(self, db_manager: DatabaseManager, conversation_tree: ConversationTree, model_name: str):
        """
        Initialize the CLI handler.
        
        Args:
            db_manager: Database manager instance
            conversation_tree: Conversation tree manager instance
            model_name: Name of the LLM model being used
        """
        super().__init__()
        self.db_manager = db_manager
        self.conversation_tree = conversation_tree
        self.model_name = model_name
        self.intro = f"Welcome to Promptree CLI! Using model: {model_name}"
        self.current_parent_id: Optional[int] = None  # Current conversation context
    
    def get_prompt(self) -> str:
        """Get the current command prompt string."""
        return f"\nPromptree|{self.model_name}|Parent:{self.current_parent_id}> "

    def start_cli(self):
        """Start the command-line interface loop."""
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
    
    def do_quit(self, arg):
        """Quit the application."""
        print("Goodbye!")
        return True  # Returning True exits the cmdloop
    
    def do_exit(self, arg):
        """Alias for quit."""
        return self.do_quit(arg)
    
    def do_rm(self, arg):
        """Remove conversations and their subtrees: rm <id>[,<id>,...]"""
        if not arg:
            print(utils.format_error("Please provide at least one conversation ID to remove."))
            return
        
        # Parse comma-separated IDs
        try:
            ids = [int(id_str.strip()) for id_str in arg.split(',')]
        except ValueError:
            print(utils.format_error("Invalid ID format. Please provide numeric IDs separated by commas."))
            return
        
        # Confirm deletion
        print(f"You are about to delete conversations with IDs: {ids}")
        print("This will also delete all their descendant conversations.")
        confirm = input("Are you sure? (yes/no): ").lower()
        
        if confirm in ['yes', 'y']:
            for conv_id in ids:
                try:
                    self.db_manager.delete_conversation(conv_id)
                    print(f"Deleted conversation {conv_id} and its subtree.")
                    
                    # If the deleted conversation was the current parent context, reset it to None
                    if self.current_parent_id == conv_id:
                        self.current_parent_id = None
                        print(f"Current parent context reset to None as conversation {conv_id} was deleted.")
                        
                except Exception as e:
                    print(utils.format_error(f"Error deleting conversation {conv_id}: {e}"))
        else:
            print("Deletion canceled.")
    
    def do_edit(self, arg):
        """Edit conversation subject, parent, and/or links: 
        edit <id> - Open conversation in external editor (plain text format) for comprehensive editing
        edit <id> -subject \"<new subject>\"
        edit <id> -parent <id|None>
        edit <id> -link <id>[,<id>,...]
        edit <id> -unlink <id>[,<id>,...]
        edit <id> -parent <id|None> -subject \"<new subject>\"
        edit <id> -subject \"<new subject>\" -parent <id|None>
        edit <id> -subject \"<new subject>\" -link <id>[,<id>,...]
        edit <id> -parent <id|None> -link <id>[,<id>,...]
        edit <id> -subject \"<new subject>\" -parent <id|None> -link <id>[,<id>,...]
        edit <id> -link None (to remove all links)
        edit <id> -subject \"<new subject>\" -unlink <id>[,<id>,...]
        edit <id> -parent <id|None> -unlink <id>[,<id>,...]
        edit <id> -subject \"<new subject>\" -parent <id|None> -unlink <id>[,<id>,...]"""
        import tempfile
        import subprocess
        import os
        
        if not arg:
            print(utils.format_error("Please provide a conversation ID and parameter(s) to edit."))
            return
        
        # Parse the command using a more flexible approach
        # Split by spaces but preserve quoted strings
        import shlex
        try:
            tokens = shlex.split(arg)
        except ValueError as e:
            print(utils.format_error(f"Invalid syntax. Error parsing arguments: {e}"))
            print(utils.format_error("Use: edit <id> [-subject \"<new subject>\"] [-parent <id|None>] [-link <id>[,<id>,...]] [-unlink <id>[,<id>,...]]"))
            return
        
        # First token should be the conversation ID
        try:
            conv_id = int(tokens[0])
        except ValueError:
            print(utils.format_error(f"Invalid conversation ID: {tokens[0]}"))
            return
        
        # Check if conversation exists
        conversation = self.db_manager.get_conversation(conv_id)
        if not conversation:
            print(utils.format_error(f"Conversation with ID {conv_id} not found."))
            return
        
        # If only conversation ID is provided without any options, open in external editor
        if len(tokens) == 1:
            self._edit_conversation_in_external_editor(conv_id, conversation)
            return
        
        if len(tokens) < 2:
            print(utils.format_error("Invalid syntax. Use: edit <id> [-subject \"<new subject>\"] [-parent <id|None>] [-link <id>[,<id>,...]] [-unlink <id>[,<id>,...]]"))
            return
        
        # Parse the options using sentinel values to distinguish "not provided" from "provided as None"
        NO_VALUE_PROVIDED = object()  # Sentinel object to differentiate
        new_subject = NO_VALUE_PROVIDED
        new_parent_id = NO_VALUE_PROVIDED
        new_links = NO_VALUE_PROVIDED
        unlink_ids = NO_VALUE_PROVIDED
        i = 1
        while i < len(tokens):
            if tokens[i] == '-subject' and i + 1 < len(tokens):
                new_subject = tokens[i + 1]
                i += 2
            elif tokens[i] == '-parent' and i + 1 < len(tokens):
                parent_arg = tokens[i + 1]
                if parent_arg.lower() in ['none', 'null']:
                    new_parent_id = None  # Actual None value
                else:
                    try:
                        new_parent_id = int(parent_arg)
                        # Validate that the new parent ID exists
                        parent_conversation = self.db_manager.get_conversation(new_parent_id)
                        if not parent_conversation:
                            print(utils.format_error(f"Parent conversation with ID {new_parent_id} not found."))
                            return
                        
                        # Check for circular reference (cannot set a child as parent)
                        if self._would_create_circular_reference(conv_id, new_parent_id):
                            print(utils.format_error(f"Cannot set parent to {new_parent_id}. This would create a circular reference."))
                            return
                    except ValueError:
                        print(utils.format_error(f"Invalid parent ID: {parent_arg}"))
                        return
                i += 2
            elif tokens[i] == '-link' and i + 1 < len(tokens):
                links_arg = tokens[i + 1]
                if links_arg.lower() in ['none', 'null']:
                    new_links = []  # Empty list means remove all links
                else:
                    try:
                        # Parse comma-separated IDs
                        link_ids = [int(id_str.strip()) for id_str in links_arg.split(',')]
                        # Validate that each linked conversation exists
                        for link_id in link_ids:
                            linked_conversation = self.db_manager.get_conversation(link_id)
                            if not linked_conversation:
                                print(utils.format_error(f"Linked conversation with ID {link_id} not found."))
                                return
                        
                        new_links = link_ids
                    except ValueError:
                        print(utils.format_error(f"Invalid link IDs: {links_arg}. Use comma-separated numeric IDs."))
                        return
                i += 2
            elif tokens[i] == '-unlink' and i + 1 < len(tokens):
                unlink_arg = tokens[i + 1]
                try:
                    # Parse comma-separated IDs to unlink
                    unlink_ids = [int(id_str.strip()) for id_str in unlink_arg.split(',')]
                    # Validate that each conversation to unlink exists
                    for unlink_id in unlink_ids:
                        unlink_conversation = self.db_manager.get_conversation(unlink_id)
                        if not unlink_conversation:
                            print(utils.format_error(f"Conversation to unlink with ID {unlink_id} not found."))
                            return
                except ValueError:
                    print(utils.format_error(f"Invalid unlink IDs: {unlink_arg}. Use comma-separated numeric IDs."))
                    return
                i += 2
            else:
                print(utils.format_error(f"Invalid syntax near: {tokens[i]}"))
                print(utils.format_error("Use: edit <id> [-subject \"<new subject>\"] [-parent <id|None>] [-link <id>[,<id>,...]] [-unlink <id>[,<id>,...]]"))
                return
        
        # Validate that at least one field is being updated
        if new_subject is NO_VALUE_PROVIDED and new_parent_id is NO_VALUE_PROVIDED and new_links is NO_VALUE_PROVIDED and unlink_ids is NO_VALUE_PROVIDED:
            print(utils.format_error("Must specify at least one field to edit: -subject, -parent, -link, or -unlink"))
            return
        
        # Update the conversation
        changes_made = []
        
        try:
            # Update subject if provided
            if new_subject is not NO_VALUE_PROVIDED:
                self.db_manager.update_subject(conv_id, new_subject)
                changes_made.append(f"Updated subject to: {utils.format_subject(new_subject)}")
            
            # Update parent if provided
            if new_parent_id is not NO_VALUE_PROVIDED:
                self.db_manager.update_conversation_parent(conv_id, new_parent_id)
                if new_parent_id is None:
                    changes_made.append(f"Updated parent to None (now root conversation)")
                else:
                    changes_made.append(f"Updated parent to {new_parent_id}")
            
            # Update links if provided
            if new_links is not NO_VALUE_PROVIDED:
                # First, remove all existing links for this conversation
                self.db_manager.remove_all_conversation_links(conv_id)
                
                # Add new links
                if new_links:  # If the list is not empty
                    for link_id in new_links:
                        # Prevent linking to itself
                        if link_id == conv_id:
                            print(utils.format_error(f"Cannot link conversation {conv_id} to itself."))
                            continue
                        self.db_manager.add_conversation_link(conv_id, link_id)
                    
                    changes_made.append(f"Updated links to: {', '.join(map(str, new_links))}")
                else:
                    changes_made.append("Removed all links")
            
            # Unlink specific conversations if provided
            if unlink_ids is not NO_VALUE_PROVIDED:
                for unlink_id in unlink_ids:
                    # Prevent unlinking from itself
                    if unlink_id == conv_id:
                        print(utils.format_error(f"Cannot unlink conversation {conv_id} from itself."))
                        continue
                    # Try to remove the link in both directions
                    try:
                        self.db_manager.remove_conversation_link(conv_id, unlink_id)
                        # Also try removing the reverse link in case it exists
                        self.db_manager.remove_conversation_link(unlink_id, conv_id)
                        changes_made.append(f"Unlinked from conversation {unlink_id}")
                    except Exception as e:
                        print(utils.format_error(f"Error unlinking from conversation {unlink_id}: {e}"))
        
            # Print results
            for change in changes_made:
                print(f"Updated conversation {conv_id} - {change}")
        
        except Exception as e:
            print(utils.format_error(f"Error updating conversation: {e}"))

    def _open_editor_with_content(self, initial_content: str, parse_function):
        """
        Open an external editor with the given content and return the modified content.
        
        Args:
            initial_content: The initial content to display in the editor
            parse_function: Function to parse the modified content
            
        Returns:
            Parsed data from the modified content
        """
        import tempfile
        import subprocess
        import os
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(initial_content)
            temp_file_path = temp_file.name
        
        try:
            # Determine the appropriate editor based on the operating system
            # Check for EDITOR environment variable first, then VISUAL, then platform defaults
            editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
            
            if not editor:
                if os.name == 'nt':  # Windows
                    # On Windows, allow user to configure their preferred editor through environment
                    # If not configured, default to notepad (original behavior)
                    # But we should provide other common Windows editors as alternatives
                    editor = 'notepad'  # Default, but users can set EDITOR env var
                else:
                    editor = 'nano'  # Default for Unix-like systems
            
            # Special handling for Windows default editor usage
            if os.name == 'nt' and editor.lower() in ['default', 'system', 'default_app', 'system_default']:
                # If user specifies a special keyword, use the system default application
                # This will use the file association for .txt files
                import time
                import os.path
                
                # Use os.startfile to open with default application
                os.startfile(temp_file_path)
                
                print("File opened with default application. Please save and close the file to continue...")
                
                # Wait for the user to finish editing by periodically checking if the file modification time has changed
                initial_mtime = os.path.getmtime(temp_file_path)
                timeout = 300  # 5 minutes timeout
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    time.sleep(2)  # Check every 2 seconds
                    try:
                        current_mtime = os.path.getmtime(temp_file_path)
                        # If modification time has changed, assume user has saved
                        if current_mtime != initial_mtime:
                            print("File has been modified. Continuing...")
                            break
                    except OSError:
                        # File might be temporarily locked during save operation
                        continue
                else:
                    print("Timeout reached. Continuing with current content...")
            else:
                # Launch the editor to edit the temporary file
                # This will block until the editor process is closed
                subprocess.run([editor, temp_file_path])
            
            # Read the modified content back from the temporary file
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                modified_content = f.read()
            
            # Parse the modified content
            parsed_data = parse_function(modified_content)
            
            return parsed_data
        
        except ValueError as e:
            print(utils.format_error(f"Error parsing text format: {e}"))
            return None
        except Exception as e:
            print(utils.format_error(f"Error processing content: {e}"))
            return None
        finally:
            # Clean up the temporary file
            try:
                os.remove(temp_file_path)
            except OSError:
                pass  # Ignore errors in removing temporary file
    
    def _edit_conversation_in_external_editor(self, conv_id: int, conversation: tuple):
        """Open conversation in external editor for comprehensive editing.
        
        Args:
            conv_id: ID of the conversation to edit
            conversation: The conversation tuple to edit
        """
        import os
        
        # Convert conversation to plain text format
        text_content = utils.conversation_to_text(conversation, self.db_manager)
        
        # Open editor with the content
        updated_data = self._open_editor_with_content(
            text_content, 
            utils.parse_conversation_text
        )
        
        # If parsing failed, return early
        if updated_data is None:
            return
            
        # Update the conversation in the database
        changes_made = []
        
        # Update subject if it changed
        if updated_data['subject'] != conversation[1]:  # subject is at index 1
            self.db_manager.update_subject(conv_id, updated_data['subject'])
            changes_made.append(f"Updated subject to: {utils.format_subject(updated_data['subject'])}")
        
        # Update parent if it changed
        if updated_data['pid'] != conversation[5]:  # pid is at index 5
            if updated_data['pid'] is not None:
                # Validate the new parent ID exists
                parent_conversation = self.db_manager.get_conversation(updated_data['pid'])
                if not parent_conversation:
                    print(utils.format_error(f"Parent conversation with ID {updated_data['pid']} not found."))
                    return
                
                # Check for circular reference
                if self._would_create_circular_reference(conv_id, updated_data['pid']):
                    print(utils.format_error(f"Cannot set parent to {updated_data['pid']}. This would create a circular reference."))
                    return
            
            self.db_manager.update_conversation_parent(conv_id, updated_data['pid'])
            if updated_data['pid'] is None:
                changes_made.append(f"Updated parent to None (now root conversation)")
            else:
                changes_made.append(f"Updated parent to {updated_data['pid']}")
        
        # Update user prompt if it changed
        if updated_data['user_prompt'] != conversation[3]:  # user_prompt is at index 3
            # For now, we just update the user prompt directly
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE conversations
                SET user_prompt = ?
                WHERE id = ?
            ''', (updated_data['user_prompt'], conv_id))
            
            conn.commit()
            conn.close()
            changes_made.append(f"Updated user prompt")
        
        # Update LLM response if it changed
        if updated_data['llm_response'] != conversation[4]:  # llm_response is at index 4
            # For now, we just update the llm_response directly
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE conversations
                SET llm_response = ?
                WHERE id = ?
            ''', (updated_data['llm_response'], conv_id))
            
            conn.commit()
            conn.close()
            changes_made.append(f"Updated LLM response")
        
        # Update linked conversations if they changed
        existing_linked_ids = set(self.db_manager.get_conversation_link_ids(conv_id))
        new_linked_ids = set(updated_data['linked_ids'])
        
        if existing_linked_ids != new_linked_ids:
            # Remove all existing links
            self.db_manager.remove_all_conversation_links(conv_id)
            
            # Add new links
            for link_id in new_linked_ids:
                # Check if the conversation to link to exists
                linked_conversation = self.db_manager.get_conversation(link_id)
                if not linked_conversation:
                    print(utils.format_error(f"Cannot link to conversation {link_id} - it does not exist."))
                    continue
                
                # Prevent linking to itself
                if link_id == conv_id:
                    print(utils.format_error(f"Cannot link conversation {conv_id} to itself."))
                    continue
                
                try:
                    self.db_manager.add_conversation_link(conv_id, link_id)
                except ValueError as e:
                    print(utils.format_error(f"Error linking to conversation {link_id}: {e}"))
            
            changes_made.append(f"Updated linked conversations to: {list(new_linked_ids)}")
        
        # Print results
        if changes_made:
            for change in changes_made:
                print(f"Updated conversation {conv_id} - {change}")
        else:
            print(f"No changes were made to conversation {conv_id}")
    
    def _would_create_circular_reference(self, conv_id: int, new_parent_id: int) -> bool:
        """Check if setting new_parent_id as parent of conv_id would create a circular reference.
        
        Args:
            conv_id: The ID of the conversation to be reparented
            new_parent_id: The ID of the potential new parent
            
        Returns:
            True if setting new_parent_id as parent would create a circular reference, False otherwise
        """
        # If we're trying to set the same conversation as its own parent, that's circular
        if conv_id == new_parent_id:
            return True
        
        # Check if new_parent_id is in the descendant chain of conv_id
        # This would create a circular reference
        descendants = self.db_manager.get_descendant_conversations(conv_id)
        for descendant in descendants:
            if descendant[0] == new_parent_id:  # descendant[0] is the ID
                return True
        
        return False

    def do_list(self, arg):
        """List top-level conversations."""
        conversations = self.db_manager.get_root_conversations()
        
        if not conversations:
            print("No top-level conversations found.")
            return
        
        print("\nTop-level conversations:")
        for conv in conversations:
            conv_id, subject, _, _, _, _, user_prompt_timestamp, _ = conv
            print(f"- {utils.format_subject(subject)} (id: {conv_id}, created on: {user_prompt_timestamp})")
        print()
    
    def do_open(self, arg):
        """Open and display a conversation tree: open <id>"""
        if not arg:
            print(utils.format_error("Please provide a conversation ID to open."))
            return
        
        try:
            conv_id = int(arg.strip())
        except ValueError:
            print(utils.format_error("Invalid conversation ID. Please provide a numeric ID."))
            return
        
        # Get the conversation details to find its parent
        conversation = self.db_manager.get_conversation(conv_id)
        if not conversation:
            print(utils.format_error(f"Conversation with ID {conv_id} not found."))
            return
        
        # Get parent conversation if it exists
        parent_id = conversation[5]  # pid is at index 5
        if parent_id is not None:
            parent_conversation = self.db_manager.get_conversation(parent_id)
            if parent_conversation:
                parent_subject = parent_conversation[1]  # subject is at index 1
                parent_timestamp = parent_conversation[6]  # user_prompt_timestamp is at index 6
                print(f"{utils.format_subject(parent_subject)} (id: {parent_id}, created on: {parent_timestamp}) [parent]")
        
        # Get the conversation tree
        tree = self.db_manager.get_conversation_tree(conv_id)
        if not tree:
            print(utils.format_error(f"Conversation with ID {conv_id} not found."))
            return
        
        # Set this as the current parent for follow-up questions
        self.current_parent_id = conv_id
        
        # Print the conversation and its tree
        self._print_conversation_tree(tree, show_full_content=True)
    
    def _print_conversation_tree(self, tree: dict, prefix: str = "", is_last: bool = True, show_full_content: bool = False):
        """Recursively print the conversation tree with ASCII tree characters.
        
        Args:
            tree: The conversation tree to print
            prefix: Prefix for the current level
            is_last: Whether this is the last child at this level
            show_full_content: Whether to show full prompt/response for all nodes or only subjects for children
        """
        # Print the current conversation
        connector = "└─ " if is_last else "├─ "
        print(f"{prefix}{connector}{utils.format_subject(tree['subject'])} (id: {tree['id']}, created on: {tree['user_prompt_timestamp']})")
        
        # Print full content if this is the main node or if we're showing everything
        if show_full_content:
            # Print user prompt and response if available
            if tree['user_prompt']:
                print(f"  {prefix}  Prompt:")
                print(f"  {prefix}  {utils.format_prompt(tree['user_prompt'])}")
            if tree['llm_response']:
                print(f"  {prefix}  Response:")
                print(f"  {prefix}  {utils.format_response(tree['llm_response'])}")
            
            # Get and display linked conversations
            linked_conversations = self.db_manager.get_linked_conversations(tree['id'])
            if linked_conversations:
                print(f"  {prefix}  Linked conversations:")
                for linked_conv in linked_conversations:
                    linked_id, linked_subject, _, _, _, _, linked_timestamp, _ = linked_conv
                    print(f"  {prefix}    • {utils.format_subject(linked_subject)} (id: {linked_id}, created on: {linked_timestamp})")
        
        # Prepare prefix for children - if we're showing full content, the children will only show subjects
        extension = "    " if is_last else "│   "
        new_prefix = prefix + extension
        
        # Recursively print children with only subject lines if we're showing full content
        children = tree['children']
        for i, child in enumerate(children):
            is_child_last = (i == len(children) - 1)
            # For children, only show subject lines unless show_full_content is False (for export)
            self._print_conversation_tree(child, new_prefix, is_child_last, show_full_content=False)
    
    def _stream_response_callback(self, response_part: str):
        """Callback function to handle streaming response parts."""
        sys.stdout.write(utils.format_response(response_part))
        sys.stdout.flush()  # Ensure the output is displayed immediately
    
    def do_ask(self, arg):
        """
        Ask a question with optional parent: ask [@<id>] <prompt> or 'ask' to open file for input
        
        Usage:
            ask [@<id>] <prompt> - Ask a question with optional parent ID
            ask - Opens an external editor to input a longer prompt and parent ID from a file
        """
        if not arg:
            # When no arguments provided, open file for input similar to edit functionality
            self._ask_via_file()
            return
        
        # Check if the prompt starts with @<id>
        match = re.match(r'^@(\d+)\s+(.+)', arg, re.DOTALL)
        if match:
            parent_id = int(match.group(1))
            prompt = match.group(2).strip()
            
            # Validate that the parent exists
            parent_conv = self.db_manager.get_conversation(parent_id)
            if not parent_conv:
                print(utils.format_error(f"Parent conversation with ID {parent_id} not found."))
                return
        else:
            # No explicit parent provided, use the current parent or create a root conversation
            parent_id = self.current_parent_id
            prompt = arg.strip()
        
        try:
            # Create the conversation with the LLM with streaming
            conv_id = self.conversation_tree.create_conversation(prompt, parent_id, self._stream_response_callback)
            
            # Add a newline after the response is complete
            print()  # Move to the next line after the streaming response
            
            # Get the created conversation to get the subject
            conversation = self.db_manager.get_conversation(conv_id)
            if conversation:
                subject = conversation[1]  # Subject is at index 1
                print(f"\nSaved conversation {conv_id} — {utils.format_subject(subject)}")
                
                # Set this as the current parent for follow-up questions
                self.current_parent_id = conv_id
            else:
                print(utils.format_error("Error: Created conversation not found in database."))
                
        except Exception as e:
            print(utils.format_error(f"Error creating conversation: {e}"))
    
    def do_add(self, arg):
        """
        Manually add a conversation through file input: add
        
        Usage:
            add - Opens an external editor to manually add a conversation with parent, links, prompt and response
        """
        # Always open file for input (no arguments version)
        self._add_via_file()
    
    def _add_via_file(self):
        """Open a temporary file for user to manually input conversation details."""
        import os
        
        # Create template content for the file with current parent ID if available
        template_content = self._create_add_file_template(parent_id=self.current_parent_id)
        
        # Open editor with the content
        parsed_data = self._open_editor_with_content(
            template_content, 
            utils.parse_add_file_content
        )
        
        # If parsing failed, return early
        if parsed_data is None:
            return
        
        parent_id = parsed_data.get('parent_id')
        user_prompt = parsed_data.get('user_prompt', '')
        llm_response = parsed_data.get('llm_response', '')
        linked_ids = parsed_data.get('linked_ids', [])
        
        # Check if the conversation has meaningful content (prompt or response)
        if not user_prompt.strip() and not llm_response.strip():
            print(utils.format_error("No meaningful content provided. Conversation not added."))
            return
        
        # Validate parent if provided
        if parent_id is not None:
            parent_conv = self.db_manager.get_conversation(parent_id)
            if not parent_conv:
                print(utils.format_error(f"Parent conversation with ID {parent_id} not found."))
                return
        
        # Validate linked conversations if provided
        for link_id in linked_ids:
            linked_conv = self.db_manager.get_conversation(link_id)
            if not linked_conv:
                print(utils.format_error(f"Linked conversation with ID {link_id} not found."))
                return
        
        # Generate a subject based on the prompt and response using the LLM
        subject = self.conversation_tree.ollama_client.generate_subject(user_prompt, llm_response)
        
        # Add the conversation to the database
        conv_id = self.db_manager.add_conversation(
            subject=subject,
            model_name=self.model_name,
            user_prompt=user_prompt,
            llm_response=llm_response,
            pid=parent_id
        )
        
        # Add links if any were specified
        for link_id in linked_ids:
            try:
                self.db_manager.add_conversation_link(conv_id, link_id)
            except ValueError as e:
                print(utils.format_error(f"Error linking conversation {conv_id} to {link_id}: {e}"))
        
        print(f"\nAdded conversation {conv_id} — {utils.format_subject(subject)}")
        
        # Set this as the current parent for follow-up questions
        self.current_parent_id = conv_id
    
    def _create_add_file_template(self, parent_id=None, linked_ids=None):
        """
        Create a template for the add command file input.
        """
        parent_id_str = str(parent_id) if parent_id is not None else ""
        linked_ids_str = ','.join(map(str, linked_ids)) if linked_ids else ""
        
        template = f"""# Add Conversation File
# Only edit the fields below. Do not change the field names.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# To update linked conversations, change LINKED_CONVERSATIONS_ID to comma-separated IDs.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'
# LLM RESPONSE section starts after 'LLM_RESPONSE_START' and ends before 'LLM_RESPONSE_END'

PARENT_ID: {parent_id_str}
LINKED_CONVERSATIONS_ID: {linked_ids_str}

USER_PROMPT_START

USER_PROMPT_END

LLM_RESPONSE_START

LLM_RESPONSE_END
---
"""
        return template
    
    def _ask_via_file(self):
        """Open a temporary file for user to input prompt and parent ID."""
        import os
        
        # Create template content for the file
        template_content = self._create_ask_file_template(self.current_parent_id)
        
        # Open editor with the content
        parsed_data = self._open_editor_with_content(
            template_content, 
            utils.parse_ask_file_content
        )
        
        # If parsing failed, return early
        if parsed_data is None:
            return
        
        # Use the parsed parent_id if provided, otherwise use current parent
        parent_id = parsed_data.get('parent_id')
        if parent_id is None:
            parent_id = self.current_parent_id
        
        prompt = parsed_data.get('user_prompt', '')
        
        if not prompt.strip():
            print(utils.format_error("No prompt provided in the file."))
            return
        
        # Validate parent if provided
        if parent_id is not None:
            parent_conv = self.db_manager.get_conversation(parent_id)
            if not parent_conv:
                print(utils.format_error(f"Parent conversation with ID {parent_id} not found."))
                return
        
        # Create the conversation with the LLM with streaming
        conv_id = self.conversation_tree.create_conversation(prompt, parent_id, self._stream_response_callback)
        
        # Add a newline after the response is complete
        print()  # Move to the next line after the streaming response
        
        # Get the created conversation to get the subject
        conversation = self.db_manager.get_conversation(conv_id)
        if conversation:
            subject = conversation[1]  # Subject is at index 1
            print(f"\nSaved conversation {conv_id} — {utils.format_subject(subject)}")
            
            # Set this as the current parent for follow-up questions
            self.current_parent_id = conv_id
        else:
            print(utils.format_error("Error: Created conversation not found in database."))

    def _create_ask_file_template(self, current_parent_id=None):
        """
        Create a template for the ask command file input.
        """
        parent_id_str = str(current_parent_id) if current_parent_id is not None else ""
        
        template = f"""# Prompt File
# Only edit the PARENT_ID and USER_PROMPT fields below.
# To remove parent, change PARENT_ID to 'None' or leave empty.
# USER PROMPT section starts after 'USER_PROMPT_START' and ends before 'USER_PROMPT_END'

PARENT_ID: {parent_id_str}
USER_PROMPT_START

USER_PROMPT_END
"""
        return template
    
    def do_export(self, arg):
        """Export conversation tree to markdown: export <id> <file>"""
        if not arg:
            print(utils.format_error("Please provide a conversation ID and output file."))
            return
        
        args = arg.split(maxsplit=1)
        if len(args) != 2:
            print(utils.format_error("Invalid syntax. Use: export <id> <file>"))
            return
        
        try:
            conv_id = int(args[0])
            output_file = args[1]
        except ValueError:
            print(utils.format_error("Invalid conversation ID. Please provide a numeric ID."))
            return
        
        # Get the conversation tree
        tree = self.db_manager.get_conversation_tree(conv_id)
        if not tree:
            print(utils.format_error(f"Conversation with ID {conv_id} not found."))
            return
        
        # Export the tree to markdown
        try:
            # Clear the file before starting
            with open(output_file, 'w', encoding='utf-8') as f:
                pass
            
            self._export_tree_to_markdown(tree, output_file)
            print(f"Exported conversation tree (ID: {conv_id}) to {output_file}")
        except Exception as e:
            print(utils.format_error(f"Error exporting conversation: {e}"))
    
    def _export_tree_to_markdown(self, tree: dict, file_path: str, level: int = 0):
        """Recursively export the conversation tree to markdown format."""
        indent = "# " + "#" * level  # Markdown heading level
        
        with open(file_path, 'a', encoding='utf-8') as f:
            # Write the subject as a heading
            f.write(f"{indent} {tree['subject']}\n\n")
            
            # Write the prompt if available
            if tree['user_prompt']:
                f.write("**Prompt:**\n")
                f.write(f"{tree['user_prompt']}\n\n")
            
            # Write the response if available
            if tree['llm_response']:
                f.write("**Response:**\n")
                f.write(f"{tree['llm_response']}\n\n")
            
            # Write metadata
            f.write(f"**ID:** {tree['id']}\n")
            f.write(f"**Model:** {tree['model_name']}\n")
            f.write(f"**Created:** {tree['user_prompt_timestamp']}\n")
            if tree['llm_response_timestamp']:
                f.write(f"**Responded:** {tree['llm_response_timestamp']}\n")
            f.write("\n---\n\n")
        
        # Recursively export children
        for child in tree['children']:
            self._export_tree_to_markdown(child, file_path, level + 1)
    
    def do_summarize(self, arg):
        """Summarize a conversation: summarize <id>"""
        if not arg:
            print(utils.format_error("Please provide a conversation ID to summarize."))
            return
        
        try:
            conv_id = int(arg.strip())
        except ValueError:
            print(utils.format_error("Invalid conversation ID. Please provide a numeric ID."))
            return
        
        # Get the conversation
        conversation = self.db_manager.get_conversation(conv_id)
        if not conversation:
            print(utils.format_error(f"Conversation with ID {conv_id} not found."))
            return
        
        # Build the content to summarize
        content_parts = []
        if conversation[3]:  # User prompt at index 3
            content_parts.append(f"User Prompt: {conversation[3]}")
        if conversation[4]:  # LLM Response at index 4
            content_parts.append(f"LLM Response: {conversation[4]}")
        
        if not content_parts:
            print("No content to summarize in this conversation.")
            return
        
        content_to_summarize = "\n\n".join(content_parts)
        
        # Generate a summary using the LLM
        try:
            summary_prompt = f"Please summarize the following conversation in bullet points:\n\n{content_to_summarize}"
            # print(f"Summary:\n", end="", flush=True)  # Start the summary line
            summary = self.conversation_tree.ollama_client.generate_response(
                summary_prompt, 
                stream_callback=self._stream_response_callback
            )
            print()  # Move to the next line after the streaming summary
        except Exception as e:
            print(utils.format_error(f"Error generating summary: {e}"))

    def do_close(self, arg):
        """Close the current conversation context: close
        Resets the current parent to None, so new 'ask' commands will create root conversations."""
        # Reset the current parent ID
        self.current_parent_id = None
        print("Current conversation context closed. New 'ask' commands will create root conversations.")

    def do_search(self, arg):
        """Search for text in conversations: search <text>
        Supports wildcard characters (*) and case-insensitive matching.
        Lists subjects of all matching conversations."""
        if not arg:
            print(utils.format_error("Please provide text to search for."))
            return
        
        # Prepare the search term for SQL LIKE query
        search_term = arg.strip()
        
        # Check if search term contains wildcards (*)
        has_wildcard = '*' in search_term
        
        # Replace * wildcard with % for SQL LIKE
        sql_search_term = search_term.replace('*', '%')
        
        # If no wildcards were provided, add % at beginning and end for partial matching
        if not has_wildcard:
            sql_search_term = f'%{sql_search_term}%'
        
        # Perform case-insensitive search in subject, user_prompt, and llm_response
        matching_conversations = self.db_manager.search_conversations(sql_search_term)
        
        if not matching_conversations:
            print(f"No conversations found containing '{search_term}'.")
            return
        
        print(f"\nFound {len(matching_conversations)} conversation(s) containing '{search_term}':")
        for conv in matching_conversations:
            conv_id, subject, _, _, _, _, user_prompt_timestamp, _ = conv
            print(f"- {utils.format_subject(subject)} (id: {conv_id}, created on: {user_prompt_timestamp})")
        print()
    
    def do_help(self, arg):
        """Show help for commands."""
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help
            print("\nPromptree CLI - Help")
            print("=" * 50)
            print("Available commands:")
            print("  quit          - Quit the application")
            print("  rm <id>[,<id>,...] - Remove conversations and their subtrees")
            print("  edit <id> - Open conversation in external editor (plain text format) for comprehensive editing")
            print("  edit <id> [-subject \"<new subject>\"] [-parent <id|None>] [-link <id>[,<id>,...]] [-unlink <id>[,<id>,...]] - Modify conversation")
            print("  list         - List top-level conversations")
            print("  open <id>    - Show conversation and its subtree")
            print("  close        - Close current conversation context, reset to root")
            print("  search <text> - Search for text in conversations (* wildcards, case-insensitive)")
            print("  ask [@<id>] <prompt> - Ask a question with optional parent")
            print("  ask - Open external editor to input a longer prompt and parent ID from a file")
            print("  add - Open external editor to manually add a conversation with parent, links, prompt and response")
            print("  export <id> <file> - Export conversation tree to markdown")
            print("  summarize <id> - Summarize a conversation")
            print("  help         - Show this help message")
            print("\nFor help with a specific command, type: help <command>")
            print()

    def emptyline(self):
        """Override empty line behavior to do nothing instead of repeating last command."""
        pass
    
    def default(self, line):
        """Handle unknown commands."""
        print(utils.format_error(f"Unknown command: {line}"))
        print("Type 'help' for available commands.")