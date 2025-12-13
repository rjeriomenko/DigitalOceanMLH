"""
DigitalOcean Gradient Agent Service

Handles communication with the DigitalOcean agent for outfit selection.
"""

import os
import json
import re
from gradient import Gradient


def select_outfit(clothing_descriptions, person_description=None, agent_access_key=None, agent_endpoint=None, model="llama3.3-70b-instruct"):
    """
    Use DigitalOcean agent to select multiple outfit combinations from clothing items.

    Args:
        clothing_descriptions: List of dicts with 'index', 'path', 'description'
        person_description: Description of the person wearing the outfits (optional)
        agent_access_key: Agent access key (optional, reads from env)
        agent_endpoint: Agent endpoint URL (optional, reads from env)
        model: Model to use (default: llama3.3-70b-instruct)

    Returns:
        list[dict]: List of outfit dictionaries, each containing:
            {
                "outfit_number": 1,
                "selected_indices": [1, 3, 5],
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

    # Build person context if provided
    person_context = ""
    if person_description:
        person_context = f"""

PERSON TO DRESS:
{person_description}

You are creating outfits specifically for this person. Consider their body type, coloring, and style when selecting items that will flatter them.
"""

    prompt = f"""I have the following clothing items in my wardrobe:

{items_text}{person_context}

Based on your expertise as a fashion stylist, please create 1-3 DIFFERENT outfit combinations from these items.

REQUIREMENTS:
- Create AT LEAST 1 outfit (always required)
- Create UP TO 3 outfits total if there are enough suitable items
- Each outfit should have 3-5 items
- Outfits should be distinct from each other (different styles, occasions, or color schemes)
- Only create multiple outfits if the wardrobe has enough variety

CRITICAL INSTRUCTION - Response Format:
Your response must have EXACTLY this format:

OUTFIT 1:
[item numbers separated by commas]
[brief 1-2 sentence explanation]

OUTFIT 2:
[item numbers separated by commas]
[brief 1-2 sentence explanation]

OUTFIT 3:
[item numbers separated by commas]
[brief 1-2 sentence explanation]

CORRECT Example:
OUTFIT 1:
2,4,5
A classic casual look with complementary earth tones and balanced proportions.

OUTFIT 2:
1,3,7
A bold streetwear ensemble featuring coordinating colors and modern silhouettes.

INCORRECT Examples:
- DO NOT include <think> tags or reasoning before the outfits
- DO NOT write explanations on the same line as item numbers
- DO NOT repeat the same items in every outfit unless necessary

Remember: Create 1-3 distinct outfits. Always label them as OUTFIT 1:, OUTFIT 2:, etc."""

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

        # Parse the response to extract multiple outfits
        outfits = parse_multiple_outfits(response_text, clothing_descriptions)

        if not outfits:
            # Fallback: if parsing fails, create one outfit with all items
            print("Warning: Could not parse agent response. Creating single outfit with all items.")
            outfits = [{
                "outfit_number": 1,
                "selected_indices": [item['index'] for item in clothing_descriptions],
                "selected_paths": [item['path'] for item in clothing_descriptions],
                "reasoning": "Using all available items (parsing failed)"
            }]

        return outfits

    except Exception as e:
        print(f"Error calling agent: {e}")
        # Fallback: use all items if agent fails
        print("Falling back to using all clothing items in single outfit...")
        return [{
            "outfit_number": 1,
            "selected_indices": [item['index'] for item in clothing_descriptions],
            "selected_paths": [item['path'] for item in clothing_descriptions],
            "reasoning": f"Agent error: {str(e)}. Using all items."
        }]


def parse_multiple_outfits(response_text, clothing_descriptions):
    """
    Parse agent response containing multiple outfits.

    Expected format:
    OUTFIT 1:
    1,2,3
    Description here

    OUTFIT 2:
    4,5,6
    Description here

    Args:
        response_text: Raw response from agent
        clothing_descriptions: List of clothing item dicts for path lookup

    Returns:
        list[dict]: List of outfit dictionaries
    """
    # Remove <think> blocks
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)

    # Split by "OUTFIT" markers
    outfit_sections = re.split(r'OUTFIT\s+(\d+):', response_text, flags=re.IGNORECASE)

    outfits = []

    # Process sections (skip first element if empty)
    for i in range(1, len(outfit_sections), 2):
        if i + 1 >= len(outfit_sections):
            break

        outfit_number = int(outfit_sections[i])
        outfit_content = outfit_sections[i + 1].strip()

        # Split into lines
        lines = [line.strip() for line in outfit_content.split('\n') if line.strip()]

        if not lines:
            continue

        # First line should be item numbers
        item_line = lines[0]
        numbers = re.findall(r'\d+', item_line)

        if not numbers:
            continue

        # Convert to unique integers
        selected_indices = list(dict.fromkeys([int(n) for n in numbers]))

        # Get paths for selected items
        selected_paths = [
            item['path'] for item in clothing_descriptions
            if item['index'] in selected_indices
        ]

        # Remaining lines are the reasoning
        reasoning = ' '.join(lines[1:]) if len(lines) > 1 else "No explanation provided"

        outfits.append({
            "outfit_number": outfit_number,
            "selected_indices": selected_indices,
            "selected_paths": selected_paths,
            "reasoning": reasoning
        })

    return outfits


def parse_agent_response(response_text):
    """
    Parse the agent's response to extract selected item numbers.

    The agent should respond with numbers on the first line (e.g., "1,3,5").
    This parser ignores any "thinking" or explanation that comes after.

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
    # Remove <think> blocks if present (some models use this for reasoning)
    import re
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)

    # Split response into lines and process
    lines = response_text.strip().split('\n')

    # Look for the first non-empty line that contains numbers
    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip lines that look like thinking/explanation (contain lots of words)
        # We want lines that are primarily numbers and commas
        word_count = len(re.findall(r'[a-zA-Z]+', line))

        # If this line has 3 or fewer words, it's likely the selection line
        if word_count <= 3:
            # Extract numbers from this line
            numbers = re.findall(r'\d+', line)
            if numbers:
                # Convert to integers and remove duplicates while preserving order
                seen = set()
                unique_numbers = []
                for n in numbers:
                    num = int(n)
                    if num not in seen:
                        seen.add(num)
                        unique_numbers.append(num)
                return unique_numbers

    # Fallback: Look for a line that's just numbers and commas/spaces
    for line in lines:
        line = line.strip()
        # Check if line is mostly numbers, commas, and spaces
        if re.match(r'^[\d,\s]+$', line):
            numbers = re.findall(r'\d+', line)
            if numbers:
                return list(dict.fromkeys([int(n) for n in numbers]))  # Remove duplicates, preserve order

    # Last resort: take numbers from first line only
    if lines:
        first_line = lines[0].strip()
        numbers = re.findall(r'\d+', first_line)
        if numbers:
            return list(dict.fromkeys([int(n) for n in numbers]))

    return []
