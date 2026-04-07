"""指标树 Pydantic 模型定义."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class RACIMatrix(BaseModel):
    """RACI 责任矩阵.
    
    R (Responsible): 执行人 - 具体执行优化任务的人
    A (Accountable): 负责人 - 对结果负最终责任的人（只能有一个）
    C (Consulted): 咨询人 - 需要提供意见的人
    I (Informed): 知会人 - 需要被告知进展的人
    """

    responsible: list[str] = Field(default_factory=list, description="执行人列表")
    accountable: Optional[str] = Field(default=None, description="负责人（唯一）")
    consulted: list[str] = Field(default_factory=list, description="需咨询的人")
    informed: list[str] = Field(default_factory=list, description="需知会的人")


class DataSource(BaseModel):
    """数据来源配置（用于 BI 只读副本连接）."""

    db_view: str = Field(..., description="BI只读视图名，如 bi_readonly.daily_gmv")
    field: str = Field(..., description="指标字段名")
    filter: Optional[str] = Field(default=None, description="SQL过滤条件模板，支持{{start}} {{end}}变量")
    agg_func: Literal["SUM", "AVG", "COUNT", "MAX", "MIN"] = Field(default="SUM", description="聚合方式")
    group_by: Optional[list[str]] = Field(default=None, description="分组字段列表")


class ChildMapping(BaseModel):
    """子节点id与数据分组取值的映射关系."""

    node_id: str
    group_value: str


class DataSliceRule(BaseModel):
    """维度切分的数据切片规则."""

    source_view: str = Field(..., description="数据来源的BI只读视图名")
    group_by_field: str = Field(..., description="用于维度切分的分组字段名")
    metric_field: str = Field(..., description="需要聚合的指标字段名")
    agg_func: Literal["SUM", "AVG", "COUNT", "MAX", "MIN"] = Field(default="SUM")
    filter_template: Optional[str] = Field(default=None, description="额外的SQL过滤模板")
    child_mapping: Optional[list[ChildMapping]] = Field(default=None, description="子节点id与数据分组取值的映射")


class Dimension(BaseModel):
    """维度池中的单个维度定义."""

    dimension_name: str = Field(..., description="维度名称，如 区域、产品、渠道")
    dimension_id: str = Field(..., description="维度唯一标识")
    child_nodes: list[str] = Field(..., description="该维度下所有子类别对应的指标树节点id列表")
    data_slice_rule: Optional[DataSliceRule] = Field(default=None, description="数据切片规则")


class TreeNode(BaseModel):
    """指标树节点."""

    id: str = Field(..., description="全局唯一标识")
    name: str = Field(..., description="指标显示名称")
    type: Literal["organization", "operation", "action"] = Field(..., description="节点类型")
    level: int = Field(..., ge=0, description="层级深度，根节点为0")
    level_code: Optional[str] = Field(default=None, description="层级编号，如 L1、L2")
    parent_id: Optional[str] = Field(default=None, description="父节点id")
    formula: Optional[str] = Field(default=None, description="精确的数学分解公式")
    pseudo_weight: Optional[float] = Field(default=None, description="无明确公式时的业务影响系数（伪权重）")
    weight: Optional[float] = Field(default=None, description="该节点在上层指标中的权重")
    entropy_threshold: float = Field(default=0.2, gt=0, lt=1, description="熵减阈值")
    data_source: Optional[DataSource] = Field(default=None, description="数据来源配置")
    permission_scope: Optional[list[str]] = Field(default=None, description="可见该节点的角色或区域代码列表")
    children: list[TreeNode] = Field(default_factory=list, description="子节点列表")
    dimension_pool: Optional[list[Dimension]] = Field(default=None, description="横向维度切分选项")
    raci: Optional[RACIMatrix] = Field(default=None, description="RACI 责任矩阵")

    @field_validator("formula")
    @classmethod
    def validate_formula_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            return None
        return v

    @model_validator(mode="after")
    def validate_action_node(self) -> TreeNode:
        if self.type == "action":
            if self.children:
                raise ValueError(f"动作指标节点 '{self.id}' 不应包含子节点")
            if self.dimension_pool:
                raise ValueError(f"动作指标节点 '{self.id}' 不应配置 dimension_pool")
        return self


class IndicatorTree(BaseModel):
    """完整的双组织指标树."""

    version: str = Field(..., description="配置文件版本号")
    root: TreeNode = Field(..., description="根节点")
