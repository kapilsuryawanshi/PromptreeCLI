import argparse
from typing import Optional
from database import DatabaseManager
from ollama_client import OllamaClient
from conversation_tree import ConversationTree
from cli import CLIHandler

def main():
    parser = argparse.ArgumentParser(description='Promptree CLI - A tool for managing LLM conversations as a tree.')
    parser.add_argument('model', help='LLM model name to use for conversations')
    
    args = parser.parse_args()
    
    # Initialize components
    db_manager = DatabaseManager()
    ollama_client = OllamaClient(model_name=args.model)
    conversation_tree = ConversationTree(db_manager, ollama_client)
    cli_handler = CLIHandler(db_manager, conversation_tree, args.model)
    
    # Start the CLI loop
    cli_handler.start_cli()

if __name__ == "__main__":
    main()