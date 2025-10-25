import cmd
import sys
import re
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
                except Exception as e:
                    print(utils.format_error(f"Error deleting conversation {conv_id}: {e}"))
        else:
            print("Deletion canceled.")
    
    def do_edit(self, arg):
        """Edit conversation subject, parent, and/or links: 
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
        
        if len(tokens) < 2:
            print(utils.format_error("Invalid syntax. Use: edit <id> [-subject \"<new subject>\"] [-parent <id|None>] [-link <id>[,<id>,...]] [-unlink <id>[,<id>,...]]"))
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
        """Ask a question with optional parent: ask [@<id>] <prompt>"""
        if not arg:
            print(utils.format_error("Please provide a prompt to ask."))
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
            print("  edit <id> [-subject \"<new subject>\"] [-parent <id|None>] [-link <id>[,<id>,...]] [-unlink <id>[,<id>,...]] - Modify conversation")
            print("  list         - List top-level conversations")
            print("  open <id>    - Show conversation and its subtree")
            print("  close        - Close current conversation context, reset to root")
            print("  search <text> - Search for text in conversations (* wildcards, case-insensitive)")
            print("  ask [@<id>] <prompt> - Ask a question with optional parent")
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