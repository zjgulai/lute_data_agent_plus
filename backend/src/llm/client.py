"""LLM API 客户端.

支持 Claude (Anthropic) 和 GPT-4 (OpenAI) 两种 LLM 后端。
开发环境可使用 Mock 客户端进行测试。
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Any

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """LLM 消息."""

    role: str = Field(..., description="角色: system / user / assistant")
    content: str = Field(..., description="消息内容")


class LLMResponse(BaseModel):
    """LLM 响应."""

    content: str
    tool_calls: Optional[list[dict[str, Any]]] = None
    usage: Optional[dict[str, int]] = None
    model: Optional[str] = None


class LLMConfig(BaseModel):
    """LLM 配置."""

    provider: str = Field(default="mock", description="llm提供商: anthropic / openai / mock")
    model: str = Field(default="claude-3-opus-20240229", description="模型名称")
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0


class BaseLLMClient(ABC):
    """LLM 客户端基类."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """调用 LLM 完成对话.

        Args:
            messages: 消息列表
            tools: 可用工具定义
            temperature: 温度参数

        Returns:
            LLM 响应
        """
        pass

    def complete_with_retry(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """带重试机制的 LLM 调用.

        Args:
            messages: 消息列表
            tools: 可用工具定义
            temperature: 温度参数

        Returns:
            LLM 响应
        """
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                return self.complete(messages, tools, temperature)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))

        raise last_error


class MockLLMClient(BaseLLMClient):
    """Mock LLM 客户端（用于开发和测试）.

    返回预设的响应，不调用真实 API。
    """

    # 预设响应模板
    RESPONSES: dict[str, str] = {
        "step1": """**Step 1: GMV 第一层拆解**

根据指标树配置，GMV 根节点下有三个候选维度：区域、产品、渠道。

正在读取各维度的波动数据...""",
        "step2": """**Step 2: 子维度熵减计算完成**

在 GMV 的候选维度中，区域维度的集中度最高（熵减 74%），意味着 GMV 的波动高度集中在某个区域。

具体看，美国区域贡献了 99% 的波动份额。相比之下，产品维度（44.5%）和渠道维度（0%）的解释力较弱。

系统建议优先从区域维度下钻到美国。点击'继续'进入下一步。""",
        "step3": """**Step 3: 动作指标定位**

继续在美国节点下钻，产品维度的熵减为 56%，A 产品占 80% 的波动份额。

已定位到关键动作指标：美国 A 产品线上广告投放预算下滑 35%（对 GMV 贡献度 -5.2%）。""",
        "step4": """**Step 4: 归因链完成**

完整归因路径：GMV -> 区域（美国）-> 产品（A产品）-> 广告预算

核心发现：美国市场 A 产品线上广告投放预算下滑 35% 是导致 GMV 下滑的主要原因。

请业务专家补充该预算削减的深层原因。""",
        "summary": """2026年3月 GMV 环比下滑 20%（-200万）。通过维度集中度分析，区域维度的熵减为 74%，解释力最强。

下钻到美国区域后，其贡献了 99% 的波动份额（-198万）。继续在美国节点下钻，产品维度的熵减为 56%，A 产品占 80%。

最终定位到动作指标：美国 A 产品线上广告投放预算下滑 35%（对 GMV 贡献度 -5.2%）。

请业务专家补充该预算削减的深层原因。""",
        "error": """**分析异常**

系统在执行算法时遇到异常，已降级为人工分析模式。

请基于现有数据，人工判断主要影响维度并补充业务结论。""",
    }

    def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Mock 实现：根据输入返回预设响应."""
        # 模拟延迟
        time.sleep(0.1)

        # 根据消息内容判断返回哪个预设响应
        content = messages[-1].content if messages else ""

        if "Step 1" in content or "第一层" in content:
            response_text = self.RESPONSES["step1"]
        elif "Step 2" in content or "子维度" in content:
            response_text = self.RESPONSES["step2"]
        elif "Step 3" in content or "动作指标" in content:
            response_text = self.RESPONSES["step3"]
        elif "Step 4" in content:
            response_text = self.RESPONSES["step4"]
        elif "异常" in content or "error" in content.lower():
            response_text = self.RESPONSES["error"]
        else:
            response_text = self.RESPONSES["summary"]

        return LLMResponse(
            content=response_text,
            tool_calls=None,
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            model="mock-llm",
        )


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude 客户端."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.api_key)
        except ImportError:
            raise ImportError("请安装 anthropic 库: pip install anthropic")

    def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """调用 Claude API."""
        # 分离 system 消息
        system_message = ""
        chat_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        kwargs = {
            "model": self.config.model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        if system_message:
            kwargs["system"] = system_message

        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        # 解析响应
        content_text = ""
        tool_calls = None

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            model=response.model,
        )


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT 客户端."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.api_base,
            )
        except ImportError:
            raise ImportError("请安装 openai 库: pip install openai")

    def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """调用 GPT API."""
        kwargs = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": 4096,
        }

        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]

        response = self.client.chat.completions.create(**kwargs)

        message = response.choices[0].message

        # 解析 tool calls
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": tc.function.arguments,
                }
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
            model=response.model,
        )


def create_llm_client(config: Optional[LLMConfig] = None) -> BaseLLMClient:
    """创建 LLM 客户端.

    Args:
        config: LLM 配置，None 则从环境变量读取

    Returns:
        LLM 客户端实例
    """
    if config is None:
        config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "mock"),
            model=os.getenv("LLM_MODEL", "claude-3-opus-20240229"),
            api_key=os.getenv("LLM_API_KEY"),
            api_base=os.getenv("LLM_API_BASE"),
        )

    if config.provider == "anthropic":
        return AnthropicClient(config)
    elif config.provider == "openai":
        return OpenAIClient(config)
    else:
        return MockLLMClient(config)
