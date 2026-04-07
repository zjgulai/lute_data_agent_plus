"""Prompt 模板.

为不同状态和模式提供 LLM Prompt 模板。
"""

from __future__ import annotations

from typing import Optional, Any


class PromptTemplate:
    """Prompt 模板管理."""

    # 系统提示词（通用）
    SYSTEM_PROMPT = """# Role
你是 GMV 智能归因系统的分析指挥官（Orchestrator）。你的任务是根据用户选择的运行模式和当前分析状态，生成清晰的自然语言说明或最终报告。

# Core Principles
1. 只读不改：你只有权读取指标树和算法规则，绝对不允许修改指标树的父子关系、权重、阈值。
2. 异常降级：如果算法返回异常或数据缺失，你必须停止自动推进，生成清晰的中文解释，并引导用户补充信息或人工介入。
3. 数据驱动：你的说明必须严格基于算法返回的数据，不能编造数字。

# Output Rules
- 如果你处于手动模式的中间步骤（Step 1~3），请用 2-3 句话简洁说明当前步骤的关键发现和下一步意图。
- 如果你处于最终汇总步骤（自动模式 Summary 或手动模式 Step 4 之后），请输出一份结构化的归因叙事，包含：关键发现、下钻路径、核心数字、待补充的业务问题。
- 如果你处于最终报告状态，输出一份可直接用于管理汇报的完整归因报告。
"""

    @classmethod
    def for_step(
        cls,
        step: int,
        mode: str,
        step_result: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """生成步骤解释 Prompt.

        Args:
            step: 步骤编号 1-4
            mode: 运行模式 auto / manual
            step_result: 该步骤的算法结果
            context: 上下文信息

        Returns:
            Prompt 文本
        """
        base = f"""# Current Context
- 任务ID: {context.get('task_id', 'unknown') if context else 'unknown'}
- 运行模式: {mode}
- 当前步骤: Step {step}
- 分析周期: {context.get('analysis_period', 'unknown') if context else 'unknown'}

# Algorithm Results (Current Step)
```json
{step_result}
```

请基于上述算法结果，生成该步骤的中文解释说明。
"""
        return base

    @classmethod
    def _format_uploaded_files(cls, uploaded_files: Optional[list[dict[str, Any]]]) -> str:
        """格式化上传文件内容为 Prompt 文本片段."""
        if not uploaded_files:
            return ""
        lines = ["\n# Uploaded Files"]
        for f in uploaded_files:
            lines.append(f"\n## {f.get('original_name', 'unknown')} ({f.get('file_type', 'unknown')})")
            content = f.get("parsed_content", "")
            if content:
                lines.append(content[:8000])  # 单文件限制 8000 字符
            else:
                lines.append("(解析中或无内容)")
        return "\n".join(lines)

    @classmethod
    def for_auto_summary(
        cls,
        attribution_chain: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
        uploaded_files: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """生成自动模式汇总 Prompt.

        Args:
            attribution_chain: 完整归因链
            context: 上下文信息
            uploaded_files: 用户上传的外部文件解析结果

        Returns:
            Prompt 文本
        """
        files_text = cls._format_uploaded_files(uploaded_files)
        return f"""# Current Context
- 任务ID: {context.get('task_id', 'unknown') if context else 'unknown'}
- 运行模式: auto
- 当前状态: 自动分析完成，生成最终汇总
- 分析周期: {context.get('analysis_period', 'unknown') if context else 'unknown'}

# Full Attribution Chain
```json
{attribution_chain}
```
{files_text}

请基于完整的归因链，生成一份结构化的归因叙事报告，包含：
1. 关键发现：GMV 波动的主要驱动因素
2. 下钻路径：从 GMV 到动作指标的完整拆解路径
3. 核心数字：各维度的熵减值和贡献度
4. 待补充：需要业务专家补充的业务结论
"""

    @classmethod
    def for_error(
        cls,
        error_state: str,
        error_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """生成异常处理 Prompt.

        Args:
            error_state: 异常状态 ALGO_ERROR / DATA_MISSING
            error_message: 错误信息
            context: 上下文信息

        Returns:
            Prompt 文本
        """
        state_desc = {
            "ALGO_ERROR": "算法执行异常",
            "DATA_MISSING": "数据缺失",
        }.get(error_state, "未知异常")

        return f"""# Current Context
- 任务ID: {context.get('task_id', 'unknown') if context else 'unknown'}
- 当前状态: 异常 - {state_desc}
- 分析周期: {context.get('analysis_period', 'unknown') if context else 'unknown'}

# Error Information
```
{error_message}
```

系统遇到异常，已降级为人工分析模式。请生成清晰的中文解释，说明：
1. 发生了什么异常
2. 可能的原因
3. 建议用户如何操作（补充数据或人工分析）
"""

    @classmethod
    def for_final_report(
        cls,
        attribution_chain: list[dict[str, Any]],
        human_conclusion: Optional[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
        uploaded_files: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """生成最终报告 Prompt.

        Args:
            attribution_chain: 完整归因链
            human_conclusion: 人工结论
            context: 上下文信息
            uploaded_files: 用户上传的外部文件解析结果

        Returns:
            Prompt 文本
        """
        conclusion_text = ""
        if human_conclusion:
            conclusion_text = f"""
# Human Conclusion
- 原因类型: {human_conclusion.get('reason_type', '')}
- 详细说明: {human_conclusion.get('detailed_explanation', '')}
- 涉及部门: {', '.join(human_conclusion.get('involved_departments', []))}
- 建议行动: {human_conclusion.get('suggested_actions', '')}
- 置信度: {human_conclusion.get('confidence_level', '')}
"""

        files_text = cls._format_uploaded_files(uploaded_files)

        return f"""# Current Context
- 任务ID: {context.get('task_id', 'unknown') if context else 'unknown'}
- 运行模式: {context.get('mode', 'unknown') if context else 'unknown'}
- 当前状态: 最终报告
- 分析周期: {context.get('analysis_period', 'unknown') if context else 'unknown'}

# Full Attribution Chain
```json
{attribution_chain}
```
{conclusion_text}
{files_text}

请生成一份可直接用于管理汇报的完整归因报告，包含：
1. 执行摘要
2. 归因分析过程
3. 关键发现
4. 业务结论（如果有）
5. 建议行动
"""
