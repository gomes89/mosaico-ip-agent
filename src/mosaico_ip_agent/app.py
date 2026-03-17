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
Main application entry point for the MOSAICO IP Agent.

This module configures and builds the FastAPI application using the MOSAICO A2A SDK.
It defines the agent's capabilities, extensions, and skills, initializes Langfuse
observability, and wires up the request handler and executor.
"""

import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="langfuse.api.core.pydantic_utilities")

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCard, AgentSkill, AgentCapabilities,
    AgentExtension
)
from fastapi import Response

from .executor import IPSolutionAgentExecutor
from .config import initialize_langfuse

langfuse = initialize_langfuse(blocked_scopes=["a2a-python-sdk"])

executor = IPSolutionAgentExecutor()

mosaico_super_task_id_extension = AgentExtension(
    uri="https://mosaico.eu/extensions/mosaico-super-task-id",
    description="Tracks interactions across agents using a mosaico-super-task-id.",
    params=None
)

agent_card = AgentCard(
    name="IP Solution Agent",
    description="IP Solution Agent for MOSAICO",
    version="1.0.0",
    protocol_version="0.3.0",
    url=f"http://{os.getenv('AGENT_CARD_HOST', "localhost")}:{os.getenv('AGENT_CARD_PORT', "8000")}/",
    capabilities=AgentCapabilities(
        streaming=False,
        extensions=[mosaico_super_task_id_extension]
    ),
    default_input_modes=['text'],
    default_output_modes=['text'],
    skills=[AgentSkill(id="ip-analysis", name="IP Analysis", description="IP Analysis",
                       tags=["ip", "license", "compliance"])]
)

request_handler = DefaultRequestHandler(
    task_store=InMemoryTaskStore(),
    agent_executor=executor
)

a2a_wrapper = A2AFastAPIApplication(
    agent_card=agent_card,
    http_handler=request_handler
)

app = a2a_wrapper.build()


@app.get("/health")
async def health():
    """
    HTTP endpoint to verify the health of the agent and its underlying LLM backend.

    Delegates the health probe to the agent executor, ensuring that the necessary
    services (like Ollama or OpenAI) are reachable and responsive.

    Returns:
        Response: A plain text HTTP response containing "OK" if healthy,
        or an error message string if the backend services are unreachable.
    """
    status = await executor.health()
    return Response(content=status, media_type="text/plain")
