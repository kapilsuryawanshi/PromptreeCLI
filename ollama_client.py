import requests
from typing import Optional, Callable
import json

class OllamaClient:
    """Handles communication with the local Ollama model."""
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama client.
        
        Args:
            model_name: Name of the LLM model to use
            base_url: Base URL of the Ollama API server (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def generate_response(self, prompt: str, context: Optional[str] = None, stream_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Generate a response from the LLM based on the given prompt and optional context.
        
        Args:
            prompt: The user's prompt
            context: Optional context history to provide to the model
            stream_callback: Optional callback function to handle streaming response chunks
            
        Returns:
            Generated response from the LLM
        """
        # Combine context and prompt if context is provided
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\nUser: {prompt}"
        
        # Prepare the request payload
        payload = {
            "model": self.model_name,
            "prompt": full_prompt + "\n\nOnly output the final answer, no other text.",
            "stream": True  # Enable streaming
        }
        
        try:
            # Make the streaming API request to Ollama
            response = requests.post(self.api_url, json=payload, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Process the streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    # Decode the line and parse as JSON
                    chunk = json.loads(line.decode('utf-8'))
                    
                    # Extract the response part
                    if "response" in chunk:
                        response_part = chunk["response"]
                        full_response += response_part
                        
                        # If we have a callback, call it with the response part
                        if stream_callback:
                            stream_callback(response_part)
                    
                    # Check if we've reached the end of the response
                    if chunk.get("done", False):
                        break
            
            return full_response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error communicating with Ollama: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Error: Invalid response format from Ollama")
    
    def generate_subject(self, prompt: str, response: str) -> str:
        """
        Generate a brief subject line for the conversation based on the prompt and response.
        
        Args:
            prompt: The user's prompt
            response: The LLM's response
            
        Returns:
            Generated subject line
        """
        subject_prompt = f"Generate a concise, informative topic name (max 50 characters) for this conversation. Only output the topic name, no extra content:<prompt>{prompt}</prompt><response>{response}</response>"
        
        subject = self.generate_response(subject_prompt)
        
        # Clean up the subject and ensure it's within reasonable length
        subject = subject.strip().replace('"', '').replace('\n', ' ')
        if len(subject) > 50:
            subject = subject[:47] + "..."
        
        return subject