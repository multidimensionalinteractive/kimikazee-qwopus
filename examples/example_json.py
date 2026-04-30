#!/usr/bin/env python3
"""
JSON mode example.

Demonstrates extracting structured JSON responses from the model.

Usage:
    python example_json.py
"""

import requests
import json
from typing import Dict, Any


def request_json_data(prompt: str, base_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """
    Request JSON-structured output from the model.
    
    Args:
        prompt: User prompt requesting structured data
        base_url: Base URL of the API
        
    Returns:
        Parsed JSON object
    """
    response = requests.post(
        f"{base_url}/v1/chat/completions",
        json={
            "model": "qwopus",
            "messages": [
                {
                    "role": "system",
                    "content": """You are a helpful assistant that outputs valid JSON.
Your response should be a single JSON object with no markdown formatting.
Never include explanations outside the JSON.
Return only raw JSON data."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for deterministic output
            "max_tokens": 2000
        }
    )
    
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    # Clean up any potential markdown formatting
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    return json.loads(content)


def extract_product_info(base_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """Extract product information as JSON."""
    return request_json_data(
        base_url,
        """Create a product entry with these details:
- name: "Wireless Bluetooth Headphones"
- brand: "TechAudio"
- price: 79.99
- category: "Electronics"
- features: ["noise-cancelling", "wireless", "40-hour battery", "quick-charge"]
- rating: 4.5
- in_stock: true"""
    )


def extract_user_profile(base_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """Extract user profile data as JSON."""
    return request_json_data(
        base_url,
        """Create a user profile with these details:
- id: "user_12345"
- name: "Sarah Johnson"
- email: "sarah@example.com"
- age: 28
- skills: ["Python", "JavaScript", "Docker", "AWS"]
- experience_years: 5
- role: "Senior Developer"
- location: "San Francisco, CA"
- preferences: {"notifications": true, "dark_mode": true}"""
    )


def extract_task_summary(base_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """Extract task analysis as JSON."""
    return request_json_data(
        base_url,
        "Analyze this task and return a structured summary: Task: Build a REST API with authentication"
    )


def main():
    """Demonstrate JSON mode capabilities."""
    print("=" * 60)
    print("Kimikazee Qwopus - JSON Mode Examples")
    print("=" * 60)
    print()
    
    # Example 1: Product Data
    print("Example 1: Product Information")
    print("-" * 40)
    try:
        product = extract_product_info()
        print(json.dumps(product, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Example 2: User Profile
    print("Example 2: User Profile")
    print("-" * 40)
    try:
        profile = extract_user_profile()
        print(json.dumps(profile, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Example 3: Custom JSON Structure
    print("Example 3: Custom JSON - Meeting Notes")
    print("-" * 40)
    try:
        meeting = request_json_data(
            base_url="http://localhost:8080",
            prompt="""Create meeting notes with these details:
- title: "Sprint Planning Q2"
- date: "2026-04-15"
- attendees: ["Alice", "Bob", "Charlie"]
- agenda: ["Review roadmap", "Assign tasks", "Discuss blockers"]
- action_items: [
    {"owner": "Alice", "task": "Update documentation", "due": "2026-04-22"},
    {"owner": "Bob", "task": "Review PRs", "due": "2026-04-20"}
  ]
- decisions: ["Adopt feature branch workflow", "Increase test coverage to 80%"]"""
        )
        print(json.dumps(meeting, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    print("=" * 60)
    print("JSON mode examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
