# MOSAICO IP Agent

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/gomes89/mosaico-ip-agent/docker-ghcr.yml?label=build)
![PyPI - Version](https://img.shields.io/pypi/v/mosaico-ip-agent)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mosaico-ip-agent)
![GitHub Release](https://img.shields.io/github/v/release/gomes89/mosaico-ip-agent)
[![REUSE status](https://api.reuse.software/badge/github.com/gomes89/mosaico-ip-agent)](https://api.reuse.software/info/github.com/gomes89/mosaico-ip-agent)
![GitHub License](https://img.shields.io/github/license/gomes89/mosaico-ip-agent)

This agent uses an LLM to parse natural language queries about software libraries, extracts package details, 
and fetches real-time licensing information from the Eclipse Foundation and ClearlyDefined APIs.

## Features

* **Provider-Agnostic Extraction:** Leverages LiteLLM to accurately extract package names, types (npm, pypi, maven), and versions. 
While optimized for Ollama, it supports 100+ LLM providers (OpenAI, Anthropic, Azure, etc.) via simple configuration changes.
* **License Verification:** Automatically queries the Eclipse Foundation and ClearlyDefined to find the declared license 
for the extracted package.
* **A2A SDK Integration:** Fully compatible with the [MOSAICO](https://gitlab.eclipse.org/eclipse-research-labs/mosaico-project) 
A2A architecture, handling task states and artifact generation.
* **Observability:** Built-in tracing and observability using Langfuse.

## Prerequisites

* **Python:** 3.10 or higher
* **Package Manager:** [uv](https://docs.astral.sh/uv/) (recommended)
* **LLM Backend:**
  * Local: Ollama (Default)
  * Remote: Any LiteLLM-supported provider (OpenAI, Claude, etc.)

## Installation

### From PyPI

```bash
pip install mosaico-ip-agent
```

### From GHCR (Docker)

```bash
docker pull ghcr.io/gomes89/mosaico-ip-agent:latest
```

### From Source (Development Only)

```bash
git clone https://github.com/gomes89/mosaico-ip-agent.git
cd mosaico-ip-agent
uv sync

# Windows:
.venv\Scripts\activate 
# Linux/macOS:
source .venv/bin/activate
```

## Configuration

The agent is configured using environment variables. You can set these in your terminal or use a .env file if you 
install a package like python-dotenv later.

| Environment Variable | Default Value              | Description                                             |
|:---------------------|:---------------------------|:--------------------------------------------------------|
| HOST                 | 0.0.0.0                    | The host IP for the Uvicorn server to bind to.          |
| PORT                 | 9000                       | The port for the Uvicorn server.                        |
| AGENT_CARD_HOST      | localhost                  | The host for the URL in the Agent Card.                 |
| AGENT_CARD_PORT      | PORT                       | The port for the URL in the Agent Card.                 |
| LLM_API_BASE         | http://localhost:11434     | The endpoint where the LLM provider is running.         |
| LLM_API_KEY          | (None)                     | The API key to access the LLM endpoint.                 |
| LLM_CONTEXT_LENGTH   | (None)                     | Explicit context window size (specifically for Ollama). |
| LLM_MODEL_NAME       | ollama/qwen2.5:0.5b        | The model identifier for LiteLLM to request.            |
| LANGFUSE_HOST        | https://cloud.langfuse.com | The base URL of the Langfuse observability server.      |
| LANGFUSE_PUBLIC_KEY  | (None/Required)            | The public key for the Langfuse observability server.   |
| LANGFUSE_SECRET_KEY  | (None/Required)            | The secret key for the Langfuse observability server.   |

## Running the Agent

Because the project is installed as a package with defined entry points, you have two simple ways to start the agent:

**Option 1: Using the CLI command**

```bash
mosaico-ip-agent
```

**Option 2: Running the module directly**

```bash
python -m mosaico_ip_agent
```

You can verify the agent is running by querying the health check endpoint:

```bash
# Linux / macOS Bash:
curl -f http://localhost:9000/health

# Windows PowerShell:
Invoke-RestMethod -Uri "http://localhost:9000/health"
```

## License

This program and the accompanying materials are made available under the terms of the MIT License, 
which is available at https://opensource.org/license/mit.
