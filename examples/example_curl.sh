#!/usr/bin/env bash
# Kimikazee Qwopus - cURL Examples
# 
# Command-line examples for interacting with the Qwopus API
# 
# Usage:
#   ./example_curl.sh
#   bash example_curl.sh

set -e

# Configuration
BASE_URL="${QWOPUS_URL:-http://localhost:8080}"

echo "============================================================"
echo "Kimikazee Qwopus - cURL Examples"
echo "============================================================"
echo "Using server: $BASE_URL"
echo ""

# Function to make a request
make_request() {
    local endpoint="$1"
    shift
    curl -s -X POST "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        "$@"
}

# Example 1: Health Check
echo "Example 1: Health Check"
echo "------------------------------------------------------------"
echo "Command:"
echo "curl $BASE_URL/health"
echo ""
echo "Result:"
curl -s "$BASE_URL/health"
echo ""
echo ""

# Example 2: List Models
echo "Example 2: List Available Models"
echo "------------------------------------------------------------"
echo "Command:"
echo "curl $BASE_URL/v1/models"
echo ""
echo "Result:"
curl -s "$BASE_URL/v1/models"
echo ""
echo ""

# Example 3: Simple Chat
echo "Example 3: Simple Chat"
echo "------------------------------------------------------------"
echo "Command:"
echo 'curl -X POST '"$BASE_URL"'/v1/chat/completions \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '\''{"model": "qwopus", "messages": [{"role": "user", "content": "What is Qwen3.5?"}], "temperature": 0.7}'\'''
echo ""
echo "Result:"
make_request "/v1/chat/completions" \
  -d '{"model": "qwopus", "messages": [{"role": "user", "content": "What is Qwen3.5?"}], "temperature": 0.7}'
echo ""
echo ""

# Example 4: Multi-turn Conversation
echo "Example 4: Multi-turn Conversation"
echo "------------------------------------------------------------"
echo "Step 1: First message"
RESPONSE1=$(make_request "/v1/chat/completions" \
  -d '{
    "model": "qwopus",
    "messages": [
      {"role": "system", "content": "You are a helpful programming assistant."},
      {"role": "user", "content": "What is Python?"}
    ]
  }')
echo "$RESPONSE1" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE1"
echo ""

# Extract assistant response for next turn
ASSISTANT_MSG=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null || echo "I'm a programming assistant!")

echo "Step 2: Follow-up question"
RESPONSE2=$(make_request "/v1/chat/completions" \
  -d '{
    "model": "qwopus",
    "messages": [
      {"role": "system", "content": "You are a helpful programming assistant."},
      {"role": "user", "content": "What is Python?"},
      {"role": "assistant", "content": "'"$ASSISTANT_MSG"'"},
      {"role": "user", "content": "How do I install it?"}
    ]
  }')
echo "$RESPONSE2" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE2"
echo ""
echo ""

# Example 5: Streaming Response (uncomment to test)
echo "Example 5: Streaming Response"
echo "------------------------------------------------------------"
echo "Uncomment the line below to test streaming:"
echo "# curl -X POST $BASE_URL/v1/chat/completions \\"
echo '#   -H "Content-Type: application/json" \\'
echo '   -d '\''{"model": "qwopus", "messages": [{"role": "user", "content": "Tell me about AI"}], "stream": true}'\'''
echo ""
echo ""

# Example 6: Custom Parameters
echo "Example 6: Custom Generation Parameters"
echo "------------------------------------------------------------"
echo "Command:"
echo 'curl -X POST '"$BASE_URL"'/v1/chat/completions \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '\''{"model": "qwopus", "messages": [{"role": "user", "content": "Write a haiku"}], "temperature": 0.9, "top_p": 0.95}'\'''
echo ""
echo "Result:"
make_request "/v1/chat/completions" \
  -d '{"model": "qwopus", "messages": [{"role": "user", "content": "Write a haiku"}], "temperature": 0.9, "top_p": 0.95}'
echo ""
echo ""

# Example 7: Pretty JSON Output
echo "Example 7: Pretty JSON Output"
echo "------------------------------------------------------------"
echo "Command:"
echo 'curl -X POST '"$BASE_URL"'/v1/chat/completions \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '\''{"model": "qwopus", "messages": [{"role": "user", "content": "Hello"}]}'\'''
echo " | python3 -m json.tool"
echo ""
echo "Result:"
make_request "/v1/chat/completions" \
  -d '{"model": "qwopus", "messages": [{"role": "user", "content": "Hello"}]}' | python3 -m json.tool 2>/dev/null || echo "(JSON parsing failed)"
echo ""
echo ""

# Example 8: Save Response to File
echo "Example 8: Save Response to File"
echo "------------------------------------------------------------"
echo "Command:"
echo 'curl -X POST '"$BASE_URL"'/v1/chat/completions \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '\''{"model": "qwopus", "messages": [{"role": "user", "content": "Generate code"}], "max_tokens": 500}'\'''
echo ' > response.json'
echo ""
echo "Execute command to save:"
curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwopus", "messages": [{"role": "user", "content": "Generate code"}], "max_tokens": 500}' > response.json
echo "Response saved to response.json"
echo ""
echo "Content:"
cat response.json
echo ""
rm -f response.json
echo ""
echo "============================================================"
echo "Examples complete!"
echo "============================================================"
