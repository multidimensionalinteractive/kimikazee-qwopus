# 📝 Kimikazee Qwopus Examples

This directory contains example code for interacting with the Kimikazee Qwopus API.

---

## Table of Contents

- [Basic Examples](#basic-examples)
  - [Python Chat Client](#python-chat-client)
  - [Node.js Client](#nodejs-client)
  - [cURL Examples](#curl-examples)
- [Advanced Examples](#advanced-examples)
  - [Streaming Response](#streaming-response)
  - [Multi-turn Conversation](#multi-turn-conversation)
  - [JSON Mode](#json-mode)
- [Swarm Examples](#swarm-examples)
  - [Multi-Agent Orchestrator](#multi-agent-orchestrator)
  - [Distributed Processing](#distributed-processing)
- [Usage Notes](#usage-notes)

---

## Basic Examples

### Python Chat Client

A simple synchronous chat client using the `requests` library.

```python
#!/usr/bin/env python3
"""
Basic chat client for Kimikazee Qwopus API.

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
        user_input = input("\nYou: ").strip()
        
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


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
pip install requests
python example_chat.py
```

---

### Node.js Client

A client using native fetch API or axios.

```javascript
/**
 * Basic chat client for Kimikazee Qwopus API.
 * 
 * Usage:
 *   node example_chat.js
 */

const BASE_URL = 'http://localhost:8080';

class QwopusChat {
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
    this.messages = [];
  }

  async chat(userMessage, systemPrompt = null) {
    // Build messages array
    const messages = [];
    
    if (systemPrompt) {
      messages.push({
        role: 'system',
        content: systemPrompt
      });
    }
    
    messages.push({
      role: 'user',
      content: userMessage
    });
    
    // Add existing conversation history
    messages.push(...this.messages);
    
    try {
      const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'qwopus',
          messages: messages,
          temperature: 0.7,
          max_tokens: 1000
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage = data.choices[0].message.content;
      
      // Store in conversation history
      this.messages.push({ role: 'user', content: userMessage });
      this.messages.push({ role: 'assistant', content: assistantMessage });
      
      return assistantMessage;
    } catch (error) {
      console.error('Error:', error);
      throw error;
    }
  }

  clearHistory() {
    this.messages = [];
  }
}

// Interactive CLI
async function main() {
  const client = new QwopusChat();
  
  console.log('='.repeat(60));
  console.log('Kimikazee Qwopus Chat');
  console.log('='.repeat(60));
  console.log("Type 'quit' or 'exit' to end the conversation");
  console.log("Type 'help' for available commands\n");

  let systemPrompt = "You are a helpful AI assistant. Be concise and accurate.";

  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const question = (query) => readline.question(query);

  while (true) {
    const userMessage = await question('\nYou: ');

    if (userMessage.toLowerCase() === 'quit' || userMessage.toLowerCase() === 'exit') {
      console.log('Goodbye!');
      break;
    }

    if (userMessage.toLowerCase() === 'help') {
      console.log(`
Available commands:
  /clear    - Clear conversation history
  /system   - Set system prompt
  /stats    - Show usage statistics
  /help     - Show this help message
      `);
      continue;
    }

    if (userMessage.toLowerCase() === '/clear') {
      client.clearHistory();
      console.log('Conversation history cleared.');
      continue;
    }

    if (userMessage.toLowerCase().startsWith('/system')) {
      systemPrompt = userMessage.slice(8).trim() || "You are a helpful AI assistant.";
      client.clearHistory();
      console.log(`System prompt set: ${systemPrompt}`);
      continue;
    }

    if (userMessage.toLowerCase() === '/stats') {
      console.log(`Messages in conversation: ${client.messages.length / 2}`);
      continue;
    }

    console.log('\nThinking...');
    try {
      const response = await client.chat(userMessage, systemPrompt);
      console.log(`\nAssistant: ${response}`);
    } catch (error) {
      console.error(`Error: ${error.message}`);
    }
  }

  readline.close();
}

main().catch(console.error);
```

**Usage:**
```bash
node example_chat.js
```

---

### cURL Examples

Command-line examples using cURL.

**Health Check:**
```bash
curl http://localhost:8080/health
```

**List Available Models:**
```bash
curl http://localhost:8080/v1/models
```

**Simple Chat:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [
      {"role": "user", "content": "What is artificial intelligence?"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

**Multi-turn Conversation:**
```bash
# First message
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [
      {"role": "system", "content": "You are a helpful programming assistant."},
      {"role": "user", "content": "What is Python?"}
    ]
  }' > response1.json

# Second message (using response from first)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [
      {"role": "system", "content": "You are a helpful programming assistant."},
      {"role": "user", "content": "What is Python?"},
      {"role": "assistant", "content": "Python is a high-level programming language..."},
      {"role": "user", "content": "How do I install it?"}
    ]
  }'
```

**Streaming Response:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [{"role": "user", "content": "Tell me about machine learning"}],
    "stream": true
  }'
```

**With Custom Parameters:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [{"role": "user", "content": "Write a poem"}],
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 50,
    "max_tokens": 200,
    "stop": ["\n\n", "END"]
  }'
```

**Pretty JSON Output:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [{"role": "user", "content": "Hello"}]
  }' | python -m json.tool
```

**Save Response to File:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [{"role": "user", "content": "Generate code"}],
    "max_tokens": 1000
  }' > response.json

# Extract just the content
cat response.json | python -m json.tool | grep -A1 '"content"' | tail -1
```

---

## Advanced Examples

### Streaming Response

Python example with real-time token streaming.

```python
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
        user_input = input("\nYou: ").strip()
        
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
            
            # Add assistant response to history
            # (In production, you'd reconstruct from tokens)
            
        except requests.exceptions.RequestException as e:
            print(f"\nError: {e}")
            messages.pop()  # Remove failed message


if __name__ == "__main__":
    main()
```

---

### Multi-turn Conversation

Example managing conversation context.

```python
#!/usr/bin/env python3
"""
Multi-turn conversation example.

Demonstrates managing conversation history and context.

Usage:
    python example_conversation.py
"""

import requests
from typing import List, Dict, Optional


class Conversation:
    """Manages multi-turn conversation state."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.messages: List[Dict] = []
        self.max_context = 50  # Maximum message history
        
    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.messages.append({
            "role": role,
            "content": content
        })
        
        # Trim if too long
        if len(self.messages) > self.max_context:
            self.messages = self.messages[-self.max_context:]
    
    def get_context(self, system_prompt: Optional[str] = None) -> List[Dict]:
        """Get conversation context, optionally with system prompt."""
        context = []
        
        if system_prompt:
            context.append({
                "role": "system",
                "content": system_prompt
            })
        
        context.extend(self.messages)
        return context
    
    def chat(self, user_message: str, **params) -> str:
        """
        Send a message and get response.
        
        Args:
            user_message: User's message
            **params: Additional request parameters
            
        Returns:
            Assistant's response
        """
        # Add user message
        self.add_message("user", user_message)
        
        # Get context
        context = self.get_context()
        
        # Make request
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "qwopus",
                "messages": context,
                "temperature": 0.7,
                **params
            }
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Get response
        assistant_message = data["choices"][0]["message"]["content"]
        
        # Add to history
        self.add_message("assistant", assistant_message)
        
        return assistant_message
    
    def clear(self) -> None:
        """Clear conversation history."""
        self.messages = []


def main():
    """Run multi-turn conversation demo."""
    conv = Conversation()
    
    print("=" * 60)
    print("Multi-turn Conversation Demo")
    print("=" * 60)
    print()
    
    # Set system prompt
    conv.chat("Hello! I'm your AI assistant.", system_prompt=True)
    
    # Example conversation
    questions = [
        "What programming languages do you know?",
        "Which one is best for data science?",
        "Can you give me a quick example?",
        "Thanks! Goodbye!"
    ]
    
    for question in questions:
        response = conv.chat(question)
        print(f"\nUser: {question}")
        print(f"Assistant: {response}")
    
    print("\n" + "=" * 60)
    print("Conversation ended!")
    print(f"Total messages: {len(conv.messages)}")


if __name__ == "__main__":
    main()
```

---

### JSON Mode

Example using response format for structured output.

```python
#!/usr/bin/env python3
"""
JSON mode example.

Demonstrates extracting structured JSON responses.

Usage:
    python example_json.py
"""

import requests
import json


def request_json_data(prompt: str) -> dict:
    """
    Request JSON-structured output from the model.
    
    Args:
        prompt: User prompt
        
    Returns:
        Parsed JSON object
    """
    response = requests.post(
        "http://localhost:8080/v1/chat/completions",
        json={
            "model": "qwopus",
            "messages": [
                {
                    "role": "system",
                    "content": """You are a helpful assistant that outputs valid JSON.
Your response should be a single JSON object with no markdown formatting.
Never include explanations outside the JSON."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {
                "type": "json_object"
            }
        }
    )
    
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    return json.loads(content)


def main():
    """Demonstrate JSON mode."""
    
    # Example 1: Product data
    print("Example 1: Product Data")
    product = request_json_data("""
    Create a product entry for a wireless mouse:
    - name: "ErgoMouse Pro"
    - price: 49.99
    - category: "Electronics"
    - features: ["wireless", "ergonomic", "RGB"]
    """)
    
    print(json.dumps(product, indent=2))
    
    # Example 2: User profile
    print("\n\nExample 2: User Profile")
    user = request_json_data("""
    Create a user profile for a developer:
    - name: "Alice Johnson"
    - age: 28
    - skills: ["Python", "JavaScript", "Docker"]
    - experience_years: 5
    """)
    
    print(json.dumps(user, indent=2))


if __name__ == "__main__":
    main()
```

---

## Swarm Examples

### Multi-Agent Orchestrator

Placeholder for multi-agent orchestration.

```python
#!/usr/bin/env python3
"""
Multi-agent swarm orchestrator (placeholder).

Future feature: Coordinate multiple agent instances for complex tasks.

Usage:
    python example_swarm.py
"""

import asyncio
from typing import List, Dict, Any


class SwarmOrchestrator:
    """
    Orchestrator for multi-agent swarms.
    
    TODO: Implement multi-agent coordination.
    
    Features to implement:
    - Task distribution across agents
    - Parallel execution
    - Result aggregation
    - Conflict resolution
    """
    
    def __init__(self, num_agents: int = 4):
        self.num_agents = num_agents
        self.agents = []
    
    async def execute(self, task: str) -> List[Dict[str, Any]]:
        """
        Execute a task using multiple agents.
        
        Args:
            task: Task description
            
        Returns:
            List of agent responses
        """
        # TODO: Implement multi-agent execution
        raise NotImplementedError(
            "Multi-agent orchestration is a future feature. "
            "Check the documentation for updates."
        )


async def main():
    """Demonstrate swarm orchestration."""
    print("Swarm orchestration is a future feature.")
    print("Check documentation for updates.")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Usage Notes

### Best Practices

1. **Error Handling:** Always check response status codes
2. **Rate Limiting:** Implement delays between requests
3. **Timeout:** Set reasonable timeouts for API calls
4. **Context:** Keep conversation context manageable
5. **Streaming:** Use streaming for better UX on long responses

### Performance Tips

- Use streaming for real-time feedback
- Set reasonable `max_tokens` limits
- Cache responses for identical queries
- Use GPU for faster inference when available
- Monitor memory usage with large contexts

---

## Related Documentation

- [API Reference](/root/repos/kimikazee-qwopus/docs/api.md)
- [Configuration Guide](/root/repos/kimikazee-qwopus/docs/configuration.md)
- [Deployment Guide](/root/repos/kimikazee-qwopus/docs/deployment.md)

---

## Support

- **GitHub Issues:** [kimikazee/kimikazee-qwopus/issues](https://github.com/kimikazee/kimikazee-qwopus/issues)
- **Documentation:** [Kimikazee Qwopus Docs](https://kimikazee.github.io/kimikazee-qwopus)

---

*Last updated: 2026-04-30 | Version: 1.0.0*
