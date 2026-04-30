#!/usr/bin/env python3
"""
Streaming chat client for Kimikazee Qwopus API.

Demonstrates real-time token streaming using Server-Sent Events (SSE).

Usage:
    python example_streaming.py
"""

import requests
import json
from typing import Iterator


def stream_chat(messages: list, base_url: str = "http://localhost:8080") -> Iterator[str]:
    """
    Stream chat responses token by token.
    
    Args:
        messages: List of chat messages
        base_url: Base URL of the API
        
    Yields:
        Individual tokens as they are generated
    """
    payload = {
        "model": "qwopus",
        "messages": messages,
        "temperature": 0.7,
        "stream": True
    }
    
    response = requests.post(
        f"{base_url}/v1/chat/completions",
        json=payload,
        stream=True
    )
    
    response.raise_for_status()
    
    for line in response.iter_lines():
        if line:
            # SSE format: "data: {...}"
            if line.startswith(b"data: "):
                data_str = line[6:].decode('utf-8')
                
                # End of stream
                if data_str == "[DONE]":
                    break
                
                try:
                    data = json.loads(data_str)
                    
                    # Get the delta content
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        
                        if content:
                            yield content
                            
                except json.JSONDecodeError:
                    continue


def main():
    """Run streaming chat session."""
    print("=" * 60)
    print("Kimikazee Qwopus - Streaming Chat")
    print("=" * 60)
    print("Type 'quit' to exit\n")
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        # Add user message
        messages.append({"role": "user", "content": user_input})
        
        print("\nAssistant: ", end="", flush=True)
        
        try:
            # Stream response
            for token in stream_chat(messages):
                print(token, end="", flush=True)
            
            print()  # Newline after response
            
        except requests.exceptions.RequestException as e:
            print(f"\nError: {e}")
            messages.pop()  # Remove failed message


if __name__ == "__main__":
    main()
