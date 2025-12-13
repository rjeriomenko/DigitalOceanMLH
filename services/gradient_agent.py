"""
DigitalOcean Gradient Agent Service

Handles communication with the DigitalOcean agent for outfit selection.
"""

import os
import json
import re
from gradient import Gradient


def select_outfit(clothing_descriptions, agent_access_key=None, agent_endpoint=None, model="llama3.3-70b-instruct"):
    """
    Use DigitalOcean agent to select the best outfit combination from clothing items.

    Args:
        clothing_descriptions: List of dicts with 'index', 'path', 'description'
        agent_access_key: Agent access key (optional, reads from env)
        agent_endpoint: Agent endpoint URL (optional, reads from env)
        model: Model to use (default: llama3.3-70b-instruct)

    Returns:
        dict: {
            "selected_indices": [1, 3, 5],  # Item numbers selected
            "selected_paths": ["path1.jpg", "path3.jpg", "path5.jpg"],
            "reasoning": "Explanation from agent"
        }

    Raises:
        ValueError: If required credentials are missing
        Exception: If agent API call fails
    """
    # Get credentials from environment if not provided
    if agent_access_key is None:
        agent_access_key = os.getenv("GRADIENT_AGENT_ACCESS_KEY")
    if agent_endpoint is None:
        agent_endpoint = os.getenv("GRADIENT_AGENT_ENDPOINT")

    if not agent_access_key or not agent_endpoint:
        raise ValueError(
            "Agent credentials not found. Set GRADIENT_AGENT_ACCESS_KEY and "
            "GRADIENT_AGENT_ENDPOINT in your .env file"
        )

    # Build the prompt with clothing descriptions
    items_text = "\n".join([
        f"{item['index']}. {item['description']}"
        for item in clothing_descriptions
    ])

    prompt = f"""I have the following clothing items in my wardrobe:

{items_text}

Based on your expertise as a fashion stylist, please select 3-5 items that create a cohesive, stylish outfit. Apply your knowledge of:
- Color coordination and color theory
- Style compatibility and aesthetic harmony
- Appropriate layering and garment combinations
- Overall visual appeal and fashion principles

Respond using this exact format:
Line 1: Selected item numbers only, separated by commas (example: 1,3,5)
Line 2: Brief 1-2 sentence explanation of your styling rationale

Example response:
2,4,5
These items create a classic casual look with complementary earth tones and balanced proportions."""

    print("\nConsulting fashion agent for outfit selection...")

    # Initialize the Gradient client with agent credentials
    try:
        agent_client = Gradient(
            agent_access_key=agent_access_key,
            agent_endpoint=agent_endpoint
        )

        # Send message to agent
        response = agent_client.agents.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=model
        )

        # Extract response text
        response_text = response.choices[0].message.content.strip()
        print(f"\nAgent response:\n{response_text}\n")

        # Parse the response to extract item numbers
        selected_indices = parse_agent_response(response_text)

        if not selected_indices:
            # Fallback: if parsing fails, use all items
            print("Warning: Could not parse agent response. Using all items.")
            selected_indices = [item['index'] for item in clothing_descriptions]

        # Get the paths for selected items
        selected_paths = [
            item['path'] for item in clothing_descriptions
            if item['index'] in selected_indices
        ]

        return {
            "selected_indices": selected_indices,
            "selected_paths": selected_paths,
            "reasoning": response_text
        }

    except Exception as e:
        print(f"Error calling agent: {e}")
        # Fallback: use all items if agent fails
        print("Falling back to using all clothing items...")
        return {
            "selected_indices": [item['index'] for item in clothing_descriptions],
            "selected_paths": [item['path'] for item in clothing_descriptions],
            "reasoning": f"Agent error: {str(e)}. Using all items."
        }


def parse_agent_response(response_text):
    """
    Parse the agent's response to extract selected item numbers.

    Handles various formats:
    - "1,3,5"
    - "Items: 1, 3, 5"
    - "1, 3, and 5"
    - Multi-line with numbers on first line

    Args:
        response_text: Raw response from agent

    Returns:
        list[int]: List of selected item indices
    """
    # Try to find numbers in the first line
    lines = response_text.strip().split('\n')
    first_line = lines[0].strip()

    # Extract all numbers from the first line
    numbers = re.findall(r'\d+', first_line)

    if numbers:
        return [int(n) for n in numbers]

    # Fallback: try to find numbers anywhere in the response
    all_numbers = re.findall(r'\d+', response_text)
    if all_numbers:
        return [int(n) for n in all_numbers]

    return []
