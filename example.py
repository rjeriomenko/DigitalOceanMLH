"""
DigitalOcean Gradient Python SDK Example

This script demonstrates basic usage of the Gradient SDK for:
- Chat completions with LLMs
- Streaming responses
- Async operations
"""

import os
from gradient import Gradient


def basic_chat_completion():
    """Example of a basic chat completion using the Gradient SDK"""
    print("=" * 50)
    print("Basic Chat Completion Example")
    print("=" * 50)

    # Initialize the Gradient client
    # The client will automatically read GRADIENT_MODEL_ACCESS_KEY from environment
    client = Gradient()

    # Create a chat completion
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is DigitalOcean Gradient?"}
        ],
        model="llama3.3-70b-instruct",
        temperature=0.7,
        max_tokens=500
    )

    # Print the response
    print(f"\nModel: {response.model}")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}")
    print()


def streaming_chat_completion():
    """Example of streaming chat completions"""
    print("=" * 50)
    print("Streaming Chat Completion Example")
    print("=" * 50)

    client = Gradient()

    print("\nStreaming response:")
    print("-" * 50)

    # Create a streaming chat completion
    stream = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Write a haiku about cloud computing."}
        ],
        model="llama3.3-70b-instruct",
        stream=True
    )

    # Process the stream
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

    print("\n" + "-" * 50)
    print()


def async_chat_completion():
    """Example of async chat completion"""
    import asyncio
    from gradient import AsyncGradient

    async def run_async():
        print("=" * 50)
        print("Async Chat Completion Example")
        print("=" * 50)

        client = AsyncGradient()

        response = await client.chat.completions.create(
            messages=[
                {"role": "user", "content": "What are the benefits of serverless AI?"}
            ],
            model="llama3.3-70b-instruct",
            temperature=0.7,
            max_tokens=300
        )

        print(f"\nResponse: {response.choices[0].message.content}")
        print()

    asyncio.run(run_async())


def embeddings_example():
    """Example of creating embeddings"""
    print("=" * 50)
    print("Embeddings Example")
    print("=" * 50)

    client = Gradient()

    # Create embeddings for text
    response = client.embeddings.create(
        input=["Hello world", "DigitalOcean Gradient is awesome!"],
        model="bge-large-en-v1.5"
    )

    print(f"\nNumber of embeddings: {len(response.data)}")
    print(f"Embedding dimensions: {len(response.data[0].embedding)}")
    print(f"First few values of first embedding: {response.data[0].embedding[:5]}")
    print()


def main():
    """Run all examples"""
    # Check if API key is set
    if not os.environ.get("GRADIENT_MODEL_ACCESS_KEY"):
        print("ERROR: GRADIENT_MODEL_ACCESS_KEY not found in environment variables.")
        print("Please set the GRADIENT_MODEL_ACCESS_KEY environment variable.")
        print("Example: export GRADIENT_MODEL_ACCESS_KEY=your_key_here")
        return

    print("\nDigitalOcean Gradient Python SDK Examples")
    print("=" * 50)
    print()

    try:
        # Run examples
        basic_chat_completion()
        streaming_chat_completion()
        async_chat_completion()
        embeddings_example()

        print("All examples completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease ensure your credentials are properly set in environment variables.")


if __name__ == "__main__":
    main()
