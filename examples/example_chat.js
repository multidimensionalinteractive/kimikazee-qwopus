/**
 * Basic chat client for Kimikazee Qwopus API.
 * 
 * A Node.js client using native fetch API.
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

  try {
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
  } catch (err) {
    if (err.code === 'ECONNREFUSED') {
      console.error('Cannot connect to server. Make sure Qwopus is running on ' + BASE_URL);
    } else {
      console.error('Interrupted:', err.message);
    }
  } finally {
    readline.close();
  }
}

// Handle uncaught errors
process.on('uncaughtException', (err) => {
  console.error('Uncaught exception:', err.message);
  process.exit(1);
});

main().catch(console.error);
