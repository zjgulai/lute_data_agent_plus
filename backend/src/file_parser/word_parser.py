"""Word 文件解析器.

使用 python-docx 提取文本内容。
"""

from __future__ import annotations

from docx import Document


class WordParser:
    """Word 文本提取器."""

    MAX_CHARS = 50000

    def parse(self, file_path: str) -> str:
        """提取 Word 文件中的文本.

        Args:
            file_path: docx 文件路径

        Returns:
            提取的文本内容
        """
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        result = "\n".join(paragraphs)
        return result[: self.MAX_CHARS]
