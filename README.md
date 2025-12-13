# DigitalOcean Gradient Python SDK Project

This project is set up to use the [DigitalOcean Gradient Python SDK](https://github.com/digitalocean/gradient-python) for building AI applications on the Gradient AI Platform.

## What is DigitalOcean Gradient?

DigitalOcean Gradient is an AI Platform that provides:
- **Serverless Inference**: Access to LLMs (Llama, Mistral, etc.) via API
- **Agent Framework**: Build and deploy AI agents
- **Knowledge Bases**: RAG (Retrieval Augmented Generation) support
- **GPU Droplets**: On-demand GPU compute resources
- **Vector Databases**: Efficient similarity search and embeddings storage

## Prerequisites

- Python 3.9 or higher
- A DigitalOcean account
- Gradient Model Access Key (obtain from [DigitalOcean Cloud](https://cloud.digitalocean.com/gradient-ai-platform))

## Setup Instructions

### 1. Clone or Navigate to Project

```bash
cd /path/to/DigitalOceanMLH
```

### 2. Activate Virtual Environment

A virtual environment is already created in `.venv`. Activate it:

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Set your credentials as environment variables:

**macOS/Linux:**
```bash
export GRADIENT_MODEL_ACCESS_KEY=your_gradient_model_access_key_here
```

**Windows (Command Prompt):**
```cmd
set GRADIENT_MODEL_ACCESS_KEY=your_gradient_model_access_key_here
```

**Windows (PowerShell):**
```powershell
$env:GRADIENT_MODEL_ACCESS_KEY="your_gradient_model_access_key_here"
```

**Optional: Using a .env file**

If you prefer to use a `.env` file, you can:
1. Copy `.env.example` to `.env` and add your credentials
2. Use a tool like [direnv](https://direnv.net/) to automatically load environment variables
3. Or manually source the file: `source .env` (after formatting it as a shell script)

**Where to get your credentials:**
- **Gradient Model Access Key**: Log in to [DigitalOcean Cloud](https://cloud.digitalocean.com/gradient-ai-platform) and navigate to the Gradient AI Platform section to generate an access key.
- **DigitalOcean Access Token** (optional, for API operations): Generate at [DigitalOcean API Tokens](https://cloud.digitalocean.com/account/api/tokens)

### 5. Run the Example

```bash
python example.py
```

This will run several examples demonstrating:
- Basic chat completions
- Streaming responses
- Async operations

## Available Models

The Gradient platform supports various models including:

- **Llama 3.3 70B Instruct** (`llama3.3-70b-instruct`) - General purpose chat
- **Llama 3.1 8B Instruct** (`llama3.1-8b-instruct`) - Smaller, faster model
- **Mistral 7B Instruct** (`mistral-7b-instruct-v0.3`) - Alternative instruction model

See the [official documentation](https://docs.digitalocean.com/products/gradient-ai-platform/) for the complete list of available models.

## Basic Usage

### Synchronous Chat Completion

```python
from gradient import Gradient

client = Gradient()

response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    model="llama3.3-70b-instruct"
)

print(response.choices[0].message.content)
```

### Streaming Response

```python
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Tell me a story"}],
    model="llama3.3-70b-instruct",
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Async Operations

```python
from gradient import AsyncGradient
import asyncio

async def main():
    client = AsyncGradient()
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello!"}],
        model="llama3.3-70b-instruct"
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Project Structure

```
DigitalOceanMLH/
├── .env                 # (Optional) Your credentials if using .env file
├── .env.example         # Template for credentials
├── .gitignore          # Git ignore rules
├── .venv/              # Python virtual environment
├── example.py          # Example usage scripts
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Resources

- [Gradient Python SDK Documentation](https://gradientai-sdk.digitalocean.com/api/python)
- [GitHub Repository](https://github.com/digitalocean/gradient-python)
- [DigitalOcean Gradient Docs](https://docs.digitalocean.com/products/gradient-ai-platform/)
- [Gradient Quickstart Guide](https://docs.digitalocean.com/products/gradient-ai-platform/getting-started/quickstart/)

## Next Steps

1. Explore the example scripts in `example.py`
2. Check out the [official documentation](https://gradientai-sdk.digitalocean.com/api/python) for more features
3. Build your AI application using the Gradient SDK
4. Try different models and parameters to optimize for your use case

## Support

- GitHub Issues: [gradient-python issues](https://github.com/digitalocean/gradient-python/issues)
- DigitalOcean Community: [community.digitalocean.com](https://community.digitalocean.com/)
- Documentation: [docs.digitalocean.com](https://docs.digitalocean.com/products/gradient-ai-platform/)

## License

This project is set up for use with the DigitalOcean Gradient Python SDK. See the [SDK's license](https://github.com/digitalocean/gradient-python/blob/main/LICENSE) for details.
