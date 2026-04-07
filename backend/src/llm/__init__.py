"""LLM 模块.

提供大模型 API 调用和 Tool Calling 功能。
"""

from __future__ import annotations

from .client import (
    LLMConfig,
    LLMMessage,
    LLMResponse,
    create_llm_client,
)
from .orchestrator import LLMOrchestrator
from .prompts import PromptTemplate
from .tools import (
    ToolCall,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    ToolResult,
    get_tool_registry,
)

__all__ = [
    # 客户端
    "LLMConfig",
    "LLMMessage",
    "LLMResponse",
    "create_llm_client",
    # Orchestrator
    "LLMOrchestrator",
    # Prompt
    "PromptTemplate",
    # Tools
    "ToolCall",
    "ToolDefinition",
    "ToolParameter",
    "ToolRegistry",
    "ToolResult",
    "get_tool_registry",
]
