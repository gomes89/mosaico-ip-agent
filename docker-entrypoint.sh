#!/bin/sh

#
# Copyright (c) 2026 André S. Gomes
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT
#

export LLM_API_BASE="${LLM_API_BASE:-${OLLAMA_BASE_URL:-${OPENAI_API_BASE:-${API_BASE}}}}"

export LLM_API_KEY="${LLM_API_KEY:-${OPENAI_API_KEY:-${API_KEY}}}"

export LLM_CONTEXT_LENGTH="${OLLAMA_CONTEXT_LENGTH:-${LLM_CONTEXT_LENGTH}}"

export LLM_MODEL_NAME="${LLM_MODEL_NAME:-${IP_AGENT_MODEL:-${MODEL_NAME}}}"

export AGENT_PORT="${IP_AGENT_PORT:-${AGENT_PORT}}"

exec "$@"
