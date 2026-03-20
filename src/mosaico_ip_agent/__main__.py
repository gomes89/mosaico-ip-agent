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
Execution entry point for the MOSAICO IP Agent module.

This script allows the agent to be executed directly from the command line
using `python -m mosaico_ip_agent`. It configures and launches the Uvicorn
server to host the FastAPI application.
"""

import os

import uvicorn

from mosaico_ip_agent.app import app


def run():
    """
    Starts the Uvicorn ASGI server to serve the FastAPI application.

    Retrieves the binding host and port from the `HOST` and `PORT`
    environment variables. If not provided, it defaults to binding on all
    interfaces (0.0.0.0) on port 9000.
    """
    host = os.getenv("HOST", "0.0.0.0")
    raw_port = os.getenv("PORT", "")
    port = int(raw_port) if raw_port.isdigit() else 9000
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
