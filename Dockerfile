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

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.14-slim AS builder

# Copy the uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Configure uv behavior:
# - UV_LINK_MODE=copy: Prevent hardlink issues across file systems
# - UV_COMPILE_BYTECODE=1: Pre-compile Python for faster startup
# - UV_PYTHON_DOWNLOADS=never: Force uv to use the system Python 3.14
# - UV_PROJECT_ENVIRONMENT=/app: Tell uv to build the virtualenv directly into /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app

WORKDIR /build

# Install dependencies using cache and bind mounts.
# We mount uv.lock and pyproject.toml temporarily so they don't bloat the layer.
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.14-slim

# Install tini for proper signal handling (CTRL+C, SIGTERM)
RUN apt-get update -qy && \
    apt-get install -qyy --no-install-recommends tini && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group for security
RUN groupadd -r app && \
    useradd -r -d /app -g app -N app

# Copy the pre-built virtual environment from the builder stage.
# We use --chown to ensure the 'app' user owns these files.
COPY --from=builder --chown=app:app /app /app

# Copy the application code and entrypoint
COPY --chown=app:app src/ /app/src/
COPY --chown=app:app docker-entrypoint.sh /docker-entrypoint.sh

# Make the entrypoint executable
RUN chmod +x /docker-entrypoint.sh

# Set the PATH to prioritize the virtual environment's binaries,
# and set PYTHONPATH so Python can find the source code.
ENV PATH="/app/bin:${PATH}" \
    PYTHONPATH="/app/src"

# Drop root privileges
USER app
WORKDIR /app

EXPOSE 9000

# Use tini as the init process to wrap the entrypoint
ENTRYPOINT ["/usr/bin/tini", "--", "/docker-entrypoint.sh"]

CMD ["python", "-m", "mosaico_ip_agent"]
