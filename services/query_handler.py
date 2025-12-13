"""
Query Handler Service

Determines whether a user query is a question (needs answer) or
an instruction (additional styling guidance for outfit generation).
"""

import os
from gradient import Gradient


def handle_query(query, clothing_descriptions, person_description=None, agent_access_key=None, agent_endpoint=None):
    """
    Process a user query to determine if it's a question or instruction.

    Args:
        query: User's text query
        clothing_descriptions: List of clothing item descriptions
        person_description: Optional person description from selfie
        agent_access_key: Agent access key (optional, reads from env)
        agent_endpoint: Agent endpoint URL (optional, reads from env)

    Returns:
        dict: {
            "type": "question" or "instruction",
            "answer": str (if question),
            "instructions": str (if instruction)
        }
    """
    # Get credentials
    if agent_access_key is None:
        agent_access_key = os.getenv("GRADIENT_AGENT_ACCESS_KEY")
    if agent_endpoint is None:
        agent_endpoint = os.getenv("GRADIENT_AGENT_ENDPOINT")

    if not agent_access_key or not agent_endpoint:
        raise ValueError("Agent credentials not found in environment")

    # Build context about available items
    items_summary = f"Available clothing items: {len(clothing_descriptions)} items including "
    item_types = [desc['description'].split(',')[0] for desc in clothing_descriptions[:5]]
    items_summary += ", ".join(item_types)
    if len(clothing_descriptions) > 5:
        items_summary += ", and more"

    person_context = ""
    if person_description:
        person_context = f"\n\nPerson information:\n{person_description}"

    # Create prompt for query classification and handling
    prompt = f"""You are a fashion AI assistant. The user has provided a query along with clothing items.

{items_summary}{person_context}

User query: "{query}"

Your task is to determine:
1. Is this a QUESTION that needs an answer? (e.g., "What would look good for a date?", "Can you explain this style?")
2. Or is this an INSTRUCTION for outfit styling? (e.g., "Make it more formal", "Focus on casual looks", "Use bright colors")

If it's a QUESTION:
- Respond with: QUESTION
- Then provide a helpful answer based on the available items

If it's an INSTRUCTION:
- Respond with: INSTRUCTION
- Then summarize the styling guidance to pass to the outfit generator

Format:
TYPE: [QUESTION or INSTRUCTION]
RESPONSE: [your answer or instruction summary]

Examples:

User: "What would look good for a casual date?"
TYPE: QUESTION
RESPONSE: Based on your wardrobe, I'd recommend pairing the blue jeans with a nice shirt and blazer for a smart-casual date look. The oxford shoes would complete the outfit nicely.

User: "Make the outfits more formal"
TYPE: INSTRUCTION
RESPONSE: Focus on formal styling - prioritize blazers, dress shoes, and structured pieces. Avoid casual items like sneakers and t-shirts.

User: "Can I wear this to work?"
TYPE: QUESTION
RESPONSE: Yes! The blazer and dress pants would make an excellent work outfit. Pair them with the dress shoes for a professional look.

User: "I want colorful, fun outfits"
TYPE: INSTRUCTION
RESPONSE: Prioritize bright colors and playful combinations. Create fun, vibrant outfits with bold color choices.

Now process the user's query."""

    try:
        # Initialize agent client
        agent_client = Gradient(
            agent_access_key=agent_access_key,
            agent_endpoint=agent_endpoint
        )

        # Get response
        response = agent_client.agents.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3.3-70b-instruct"
        )

        response_text = response.choices[0].message.content.strip()

        # Parse response
        lines = response_text.split('\n')
        query_type = None
        response_content = ""

        for line in lines:
            line = line.strip()
            if line.startswith("TYPE:"):
                type_value = line.replace("TYPE:", "").strip().upper()
                if "QUESTION" in type_value:
                    query_type = "question"
                elif "INSTRUCTION" in type_value:
                    query_type = "instruction"
            elif line.startswith("RESPONSE:"):
                response_content = line.replace("RESPONSE:", "").strip()

        # Collect remaining lines as part of response if multiline
        if "RESPONSE:" in response_text:
            response_start = response_text.index("RESPONSE:") + len("RESPONSE:")
            response_content = response_text[response_start:].strip()

        # Return result
        if query_type == "question":
            return {
                "type": "question",
                "answer": response_content or "I can help you with that based on your wardrobe!"
            }
        elif query_type == "instruction":
            return {
                "type": "instruction",
                "instructions": response_content or query
            }
        else:
            # Fallback: treat as instruction if unclear
            return {
                "type": "instruction",
                "instructions": query
            }

    except Exception as e:
        print(f"Error in query handler: {e}")
        # Fallback: treat as instruction
        return {
            "type": "instruction",
            "instructions": query
        }
