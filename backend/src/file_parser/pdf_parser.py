"""PDF 文件解析器.

使用 PyPDF2 提取文本内容。
"""

from __future__ import annotations

from typing import Optional

from PyPDF2 import PdfReader


class PDFParser:
    """PDF 文本提取器."""

    MAX_CHARS = 50000

    def parse(self, file_path: str) -> str:
        """提取 PDF 文件中的文本.

        Args:
            file_path: PDF 文件路径

        Returns:
            提取的文本内容
        """
        reader = PdfReader(file_path)
        parts: list[str] = []
        total_length = 0

        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
                total_length += len(text)
                if total_length >= self.MAX_CHARS:
                    break

        result = "\n\n".join(parts)
        return result[: self.MAX_CHARS]
