"""Excel 文件解析器.

使用 pandas 提取前 N 行并转换为 Markdown 表格。
"""

from __future__ import annotations

import pandas as pd


class ExcelParser:
    """Excel 文本提取器."""

    MAX_ROWS = 100
    MAX_CHARS = 30000

    def parse(self, file_path: str) -> str:
        """提取 Excel 文件中的内容.

        Args:
            file_path: Excel 文件路径

        Returns:
            Markdown 表格格式的文本内容
        """
        df = pd.read_excel(file_path, nrows=self.MAX_ROWS)

        # 清洗数据：替换 NaN 为空字符串
        df = df.fillna("")

        # 转换为 Markdown 表格
        lines = []
        headers = [str(h) for h in df.columns.tolist()]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for _, row in df.iterrows():
            row_values = [str(v) for v in row.tolist()]
            lines.append("| " + " | ".join(row_values) + " |")

        result = "\n".join(lines)
        return result[: self.MAX_CHARS]
