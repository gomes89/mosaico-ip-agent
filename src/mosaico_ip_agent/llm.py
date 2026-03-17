#  Copyright (c) 2026 André S. Gomes
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of
#  this software and associated documentation files (the "Software"), to deal in
#  the Software without restriction, including without limitation the rights to
#  use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
#  the Software, and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#  FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#  IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  SPDX-License-Identifier: MIT

"""
LLM agent integration for extracting software package information.

This module provides the IPSolutionAgent class, which uses LiteLLM to interface
with various LLM providers (Ollama, OpenAI, Anthropic, etc.) to parse natural
language queries into structured package data (name, type, version).
"""

import os
from typing import Dict, Any

import litellm

from .config import initialize_langfuse


class IPSolutionAgent:
    """
    Agent responsible for parsing natural language queries to extract software
    package details (name, type, version) using a configured LLM backend.
    """

    def __init__(self):
        """
        Initializes the IPSolutionAgent with normalized environment variables.

        Pulls configuration for the LLM model, API base URL, API key, and context length.
        These variables are expected to be normalized by the Docker entrypoint script.
        It also configures LiteLLM to use Langfuse for observability callbacks.
        """
        self.llm_api_base = os.getenv('LLM_API_BASE', 'http://localhost:11434')
        self.llm_api_key = os.getenv('LLM_API_KEY', None)
        self.llm_model_name = os.getenv('LLM_MODEL_NAME', 'ollama/qwen2.5:0.5b')
        self.llm_context_length = os.getenv('LLM_CONTEXT_LENGTH', None)
        self.langfuse = initialize_langfuse()

        # Configure LiteLLM to use Langfuse callbacks globally
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]

    async def run(self, query: str, mosaico_super_task_id: str = None) -> Dict[str, Any]:
        """
        Executes the extraction prompt against the configured LLM backend.

        Constructs a strict extraction prompt based on the user's natural language query,
        injects MOSAICO tracing metadata, and handles provider-specific arguments like
        Ollama's context length.

        Args:
            query (str): The natural language query containing software package information.
            mosaico_super_task_id (str, optional): The trace ID for MOSAICO A2A SDK tracking. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'content' (str): The raw extracted string formatted as "name|type|version", or an error message.
                - 'success' (bool): True if the LLM call succeeded, False otherwise.
        """
        metadata = {
            "mosaico_super_task_id": mosaico_super_task_id,
            "project_name": "ip-solution-agent",
            "trace_name": "extract-package-info"
        }

        if mosaico_super_task_id:
            metadata["trace_id"] = mosaico_super_task_id

        prompt = (
            "Instructions: Extract only the library name, type, and version.\n"
            "Format: name|type|version\n"
            "Types: npm, pypi, maven (Strictly use these labels only)\n"
            "Default version: if not provided by the input, use -\n\n"
            "Input: Check the pypi package requests\n"
            "Output: requests|pypi|-\n\n"
            "Input: find the npm package react version 18\n"
            "Output: react|npm|18\n\n"
            "Input: lookup the maven library junit v6.1.0\n"
            "Output: junit|maven|6.1.0\n\n"
            f"Input: {query}\n"
            "Output:"
        )

        kwargs = {}
        if self.llm_context_length:
            kwargs["extra_body"] = {"num_ctx": int(self.llm_context_length)}

        try:
            response = await litellm.acompletion(
                model=self.llm_model_name,
                messages=[{"role": "user", "content": prompt}],
                api_base=self.llm_api_base,
                api_key=self.llm_api_key,
                max_tokens=30,
                temperature=0,
                metadata=metadata,
                timeout=30,
                **kwargs
            )
            return {"content": response.choices[0].message.content.strip(), "success": True}
        except Exception as e:
            return {"content": str(e), "success": False}

    async def health(self) -> str:
        """
        Performs a functional health check against the LLM backend.

        Sends a minimal 'ping' prompt to verify end-to-end connectivity, authentication,
        and model availability within a strict 5-second timeout.

        Returns:
            str: "OK" if the LLM responds successfully, otherwise a string starting
            with "Unhealthy:" followed by the exception details.
        """
        try:
            # A lightweight prompt to verify the LLM is functional
            await litellm.acompletion(
                model=self.llm_model_name,
                messages=[{"role": "user", "content": "ping"}],
                api_base=self.llm_api_base,
                api_key=self.llm_api_key,
                max_tokens=5,
                timeout=5  # Ensure the health check doesn't hang indefinitely
            )
            return "OK"
        except Exception as e:
            print(f"Health check failed - LLM unreachable or error: {e}")
            return f"Unhealthy: {str(e)}"
