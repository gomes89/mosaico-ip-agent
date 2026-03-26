"""Shared Langfuse initialization helpers for all agents."""

from __future__ import annotations

from typing import Sequence

from langfuse import Langfuse


def initialize_langfuse(
        *,
        blocked_scopes: Sequence[str] | None = None,
        **client_kwargs: object,
) -> Langfuse | None:
    """Create a Langfuse client with consistent configuration."""
    scopes = list(blocked_scopes) if blocked_scopes else None

    try:
        client = Langfuse(
            blocked_instrumentation_scopes=scopes,
            **client_kwargs,
        )
        if client.auth_check():
            print("Langfuse client is authenticated and ready!")
            return client
        else:
            print("Langfuse authentication failed. Agent will start without observability.")
            return None
    except Exception as e:
        print(f"Langfuse initialization failed: {e}. Agent will start without observability.")
        return None


__all__ = ["initialize_langfuse"]
