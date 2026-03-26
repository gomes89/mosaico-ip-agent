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
Agent execution logic for the MOSAICO IP Agent.

This module provides the execution orchestration, bridging the natural language
parsing from the LLM with the license verification services, and reporting
the progress and artifacts back through the MOSAICO A2A event queue.
"""

from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    TaskState, TaskStatus, TaskStatusUpdateEvent, TaskArtifactUpdateEvent,
    Artifact, Part, TextPart, DataPart, Message, Role
)
from a2a.utils import new_task
from typing_extensions import override

from .llm import IPSolutionAgent
from .services import query_eclipse_foundation, query_clearly_defined


class IPSolutionAgentExecutor(AgentExecutor):
    """
    Executes Intellectual Property (IP) analysis tasks within the MOSAICO A2A framework.

    This executor coordinates the workflow of extracting package details from user
    queries via an LLM agent, verifying license information against external
    sources (Eclipse Foundation, ClearlyDefined), and emitting structured artifacts
    and state updates to the event queue.
    """

    def __init__(self):
        """
        Initializes the IPSolutionAgentExecutor.

        Instantiates the underlying LLM agent responsible for parsing natural
        language package queries.
        """
        self.agent = IPSolutionAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Executes the IP analysis workflow for a given request context.

        Processes the user's natural language query to extract library details,
        looks up the declared license for the package, and enqueues the resulting
        artifacts (JSON data and text explanation) back to the client. It also
        manages the task lifecycle (creation, metadata tracking, and final status).

        Args:
            context (RequestContext): The execution context containing the user's
                input, current task metadata, and tracing IDs.
            event_queue (EventQueue): The asynchronous queue used to dispatch
                state updates and artifacts back to the MOSAICO system.

        Raises:
            Exception: Captures internal extraction errors, dispatching them
                as failure events to the client rather than crashing the executor.
        """
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        if hasattr(context.message, 'metadata') and context.message.metadata:
            m_id = context.message.metadata.get('mosaico_super_task_id')
            if m_id:
                if not task.metadata:
                    task.metadata = {}
                task.metadata['mosaico-super-task-id'] = m_id

        m_super_id = task.metadata.get('mosaico-super-task-id') if task.metadata else None

        try:
            result = await self.agent.run(query, m_super_id)
            if not result["success"]:
                raise Exception(result["content"])

            parts = [p.strip() for p in result["content"].split("|")]
            if len(parts) < 2 or parts[0].lower() == "error":
                explanation = f"Extraction failure: {result['content']}"
                task_state = TaskState.failed
            else:
                name, p_type, version = parts[0], parts[1], parts[2]
                providers = {"npm": "npmjs", "pypi": "pypi", "maven": "mavencentral"}
                provider = providers.get(p_type.lower(), "-")
                namespace = '-'

                res = await query_eclipse_foundation(p_type, provider, namespace, name, version)
                if not res:
                    res = await query_clearly_defined(p_type, provider, namespace, name, version)

                if isinstance(res, dict):
                    explanation = (
                        f"Analyzed {name} ({p_type}/{provider}/{namespace}) with version {version}. "
                        f"The license is: {res['license']} "
                        f"[Source: {res['source']}]."
                    )
                    sol_artifact = Artifact(
                        parts=[
                            Part(root=DataPart(data={
                                "name": name,
                                "type": p_type,
                                "provider": provider,
                                'namespace': namespace,
                                "version": version,
                                "license": res["license"],
                                "source": res["source"]
                            }))
                        ],
                        artifact_id='ip_analysis_result'
                    )
                    await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                        context_id=task.context_id, task_id=task.id, artifact=sol_artifact
                    ))
                    task_state = TaskState.completed
                else:
                    explanation = f"Package {name} not found."
                    task_state = TaskState.failed

            await event_queue.enqueue_event(Message(
                message_id=str(uuid4()),
                context_id=task.context_id,
                task_id=task.id,
                role=Role.agent,
                parts=[Part(root=TextPart(text=explanation))]
            ))

        except Exception as e:
            await event_queue.enqueue_event(Message(
                message_id=str(uuid4()),
                context_id=task.context_id,
                task_id=task.id,
                role=Role.agent,
                parts=[Part(root=TextPart(text=str(e)))]
            ))
            task_state = TaskState.failed

        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            context_id=task.context_id, task_id=task.id,
            status=TaskStatus(state=task_state), final=True
        ))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Handles cancellation requests for the current execution.

        Currently implemented as a pass-through (no-op), as the underlying LLM
        and HTTP requests are typically short-lived and resolve before cancellation
        becomes necessary.

        Args:
            context (RequestContext): The context of the request to be canceled.
            event_queue (EventQueue): The queue for emitting cancellation events.
        """
        pass

    async def health(self) -> str:
        """
        Performs a health check on the executor's dependencies.

        Delegates the health probe to the underlying LLM agent to ensure
        the AI provider is reachable and responsive.

        Returns:
            str: "OK" if the underlying agent is healthy, or an error description
            if the services are unreachable.
        """
        return await self.agent.health()
