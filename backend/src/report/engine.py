"""报告生成引擎.

统一入口，根据报告类型和格式调度具体生成器。
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from .pdf_generator import PDFReportGenerator
from .word_generator import WordReportGenerator


class ReportType(str, Enum):
    """报告类型."""

    PROCESS = "process"
    FULL = "full"


class ReportFormat(str, Enum):
    """报告格式."""

    WORD = "word"
    PDF = "pdf"


class ReportEngine:
    """报告生成引擎."""

    def __init__(self) -> None:
        """初始化生成器."""
        self.word_gen = WordReportGenerator()
        self.pdf_gen = PDFReportGenerator()

    async def generate(
        self,
        session_data: dict[str, Any],
        report_type: ReportType,
        report_format: ReportFormat,
    ) -> bytes:
        """生成报告.

        Args:
            session_data: 会话完整数据
            report_type: 报告类型
            report_format: 报告格式

        Returns:
            报告文件字节内容
        """
        title = self._get_title(session_data, report_type)

        if report_format == ReportFormat.WORD:
            return self.word_gen.generate(title, session_data, report_type.value)

        if report_format == ReportFormat.PDF:
            return await self.pdf_gen.generate(title, session_data, report_type.value)

        raise ValueError(f"不支持的报告格式: {report_format}")

    def _get_title(self, session_data: dict[str, Any], report_type: ReportType) -> str:
        """生成报告标题."""
        base = "GMV 智能归因报告"
        if report_type == ReportType.PROCESS:
            return f"{base} — 过程报告"
        return f"{base} — 完整报告"
