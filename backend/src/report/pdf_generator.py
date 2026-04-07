"""PDF 报告生成器.

使用 Playwright 将 HTML 模板渲染为 PDF。
"""

from __future__ import annotations

import os
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright


# 模板目录
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


class PDFReportGenerator:
    """PDF 报告生成器."""

    def __init__(self) -> None:
        """初始化 Jinja2 模板环境."""
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def generate(
        self,
        title: str,
        session_data: dict[str, Any],
        report_type: str,
    ) -> bytes:
        """生成 PDF 报告并返回字节内容.

        Args:
            title: 报告标题
            session_data: 会话完整数据
            report_type: 报告类型 (process / full)

        Returns:
            PDF 文件的字节内容
        """
        template = self.env.get_template("report_template.html")

        confidence_map = {
            "high": "高",
            "medium": "中",
            "low": "低",
        }
        conclusion = session_data.get("conclusion")
        if conclusion:
            conclusion = dict(conclusion)
            conclusion["confidence_level_label"] = confidence_map.get(
                conclusion.get("confidence_level", ""), "-"
            )

        html_content = template.render(
            title=title,
            report_type=report_type,
            session_id=session_data.get("session_id", "-"),
            start_date=session_data.get("start_date", "-"),
            end_date=session_data.get("end_date", "-"),
            generated_at=session_data.get("generated_at", "-"),
            analysis_mode=session_data.get("analysis_mode", "-"),
            current_state=session_data.get("current_state", "-"),
            comparison_period=session_data.get("comparison_period", "-"),
            steps=session_data.get("steps", []),
            conclusion=conclusion,
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                format="A4",
                margin={"top": "40px", "right": "40px", "bottom": "40px", "left": "40px"},
                print_background=True,
            )
            await browser.close()

        return pdf_bytes
