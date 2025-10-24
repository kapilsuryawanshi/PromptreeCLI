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