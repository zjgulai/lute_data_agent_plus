"""Tool Calling 定义.

定义 LLM Orchestrator 可调用的工具集合。
"""

from __future__ import annotations

from typing import Optional, Any, Callable

from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """工具参数定义."""

    name: str
    type: str
    description: str
    required: bool = True


class ToolDefinition(BaseModel):
    """工具定义."""

    name: str
    description: str
    parameters: list[ToolParameter]


class ToolCall(BaseModel):
    """工具调用请求."""

    tool: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """工具调用结果."""

    tool: str
    success: bool
    result: Any = None
    error: Optional[str] = None


# ============ 工具定义 ============

READ_EXCEL_DATA_TOOL = ToolDefinition(
    name="read_excel_data",
    description="读取 Excel 文件中的数据，支持过滤和字段选择",
    parameters=[
        ToolParameter(name="file", type="string", description="Excel 文件路径"),
        ToolParameter(name="sheet", type="string", description="工作表名称"),
        ToolParameter(name="fields", type="array", description="需要读取的字段列表"),
        ToolParameter(name="filter", type="string", description="过滤条件（可选）"),
    ],
)

CALCULATE_ENTROPY_REDUCTION_TOOL = ToolDefinition(
    name="calculate_entropy_reduction",
    description="计算维度熵减，选择最佳切分维度",
    parameters=[
        ToolParameter(name="task_id", type="string", description="任务ID"),
        ToolParameter(name="parent_node_id", type="string", description="父节点ID"),
        ToolParameter(
            name="candidate_dimensions",
            type="array",
            description="候选维度列表，每个维度包含 dimension_name 和 child_nodes",
        ),
        ToolParameter(name="raw_data", type="object", description="原始数据", required=False),
    ],
)

CHECK_CROSS_DIMENSION_TOOL = ToolDefinition(
    name="check_cross_dimension",
    description="执行交叉维度校验，检查维度组合的影响",
    parameters=[
        ToolParameter(name="task_id", type="string", description="任务ID"),
        ToolParameter(name="parent_node_id", type="string", description="父节点ID"),
        ToolParameter(name="dimension_pairs", type="array", description="维度组合列表，如[['区域', '产品']]"),
        ToolParameter(name="raw_data", type="object", description="原始数据", required=False),
    ],
)

REQUEST_HUMAN_INPUT_TOOL = ToolDefinition(
    name="request_human_input",
    description="请求用户输入业务结论",
    parameters=[
        ToolParameter(name="prompt", type="string", description="提示用户的问题"),
        ToolParameter(name="context", type="object", description="上下文信息", required=False),
    ],
)

# 所有可用工具
AVAILABLE_TOOLS: list[ToolDefinition] = [
    READ_EXCEL_DATA_TOOL,
    CALCULATE_ENTROPY_REDUCTION_TOOL,
    CHECK_CROSS_DIMENSION_TOOL,
    REQUEST_HUMAN_INPUT_TOOL,
]


class ToolRegistry:
    """工具注册表.

    管理工具的定义和执行函数。
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable] = {}

    def register(
        self,
        definition: ToolDefinition,
        handler: Callable[..., Any],
    ) -> None:
        """注册工具.

        Args:
            definition: 工具定义
            handler: 工具执行函数
        """
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def get_definition(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义."""
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        """获取工具执行函数."""
        return self._handlers.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """列出所有工具."""
        return list(self._tools.values())

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用.

        Args:
            tool_call: 工具调用请求

        Returns:
            工具执行结果
        """
        handler = self._handlers.get(tool_call.tool)
        if not handler:
            return ToolResult(
                tool=tool_call.tool,
                success=False,
                error=f"未知工具: {tool_call.tool}",
            )

        try:
            result = handler(**tool_call.arguments)
            return ToolResult(
                tool=tool_call.tool,
                success=True,
                result=result,
            )
        except Exception as e:
            return ToolResult(
                tool=tool_call.tool,
                success=False,
                error=str(e),
            )


# 全局工具注册表
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
