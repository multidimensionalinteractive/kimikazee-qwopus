#!/usr/bin/env python3
"""
Basic chat client for Kimikazee Qwopus API.

A simple synchronous chat client demonstrating basic API usage.

Usage:
    python example_chat.py
"""

import requests
import json
from typing import Optional


class QwopusChat:
    """Simple client for interacting with Qwopus API."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the chat client.
        
        Args:
            base_url: Base URL of the Qwopus API server
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: str = "qwopus"
    ) -> dict:
        """
        Send a chat request and get a response.
        
        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            model: Model identifier
            
        Returns:
            API response dictionary
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def chat_simple(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """
        Simple chat interface for single questions.
        
        Args:
            user_message: User's message
            system_prompt: Optional system prompt
            
        Returns:
            Assistant's response
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        response = self.chat(messages)
        return response["choices"][0]["message"]["content"]


def main():
    """Run interactive chat session."""
    client = QwopusChat("http://localhost:8080")
    
    print("=" * 60)
    print("Kimikazee Qwopus Chat")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'help' for available commands")
    print()
    
    messages = []
    system_prompt = "You are a helpful AI assistant. Be concise and accurate."
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if user_input.lower() == 'help':
            print("""
Available commands:
  /clear    - Clear conversation history
  /system   - Set system prompt
  /stats    - Show usage statistics
  /help     - Show this help message
            """)
            continue
        
        if user_input.lower() == '/clear':
            messages = []
            print("Conversation history cleared.")
            continue
        
        if user_input.lower() == '/stats':
            print(f"Messages in conversation: {len(messages)}")
            continue
        
        if user_input.lower().startswith('/system'):
            system_prompt = user_input[8:].strip() or "You are a helpful AI assistant."
            messages = []
            print(f"System prompt set: {system_prompt}")
            continue
        
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Get response
            response = client.chat(messages, temperature=0.7)
            assistant_message = response["choices"][0]["message"]["content"]
            
            # Display response
            print(f"\nAssistant: {assistant_message}")
            
            # Add assistant response to history
            messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            messages.pop()  # Remove failed message


if __name__ == "__main__":
    main()
