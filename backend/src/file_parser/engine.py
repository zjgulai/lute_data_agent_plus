"""文件解析引擎.

统一入口，根据文件类型调度具体解析器。
"""

from __future__ import annotations

import os
from typing import Optional

from .excel_parser import ExcelParser
from .pdf_parser import PDFParser
from .word_parser import WordParser


class FileParseError(Exception):
    """文件解析错误."""

    pass


class FileParser:
    """统一文件解析器."""

    def __init__(self) -> None:
        """初始化各类型解析器."""
        self.pdf = PDFParser()
        self.word = WordParser()
        self.excel = ExcelParser()

    def parse(self, file_path: str, file_type: Optional[str] = None) -> str:
        """解析文件并返回文本内容.

        Args:
            file_path: 文件路径
            file_type: 文件类型 (pdf / word / excel)，为 None 时从后缀推断

        Returns:
            解析后的文本内容

        Raises:
            FileParseError: 不支持的文件类型或解析失败
        """
        ext = (file_type or os.path.splitext(file_path)[1].lower().lstrip("."))

        try:
            if ext == "pdf":
                return self.pdf.parse(file_path)
            if ext in ("docx", "word"):
                return self.word.parse(file_path)
            if ext in ("xlsx", "xls", "excel"):
                return self.excel.parse(file_path)
        except Exception as e:
            raise FileParseError(f"解析失败 ({ext}): {e}") from e

        raise FileParseError(f"不支持的文件类型: {ext}")


def parse_file(file_path: str, file_type: Optional[str] = None) -> str:
    """便捷函数：解析文件.

    Args:
        file_path: 文件路径
        file_type: 文件类型

    Returns:
        解析后的文本内容
    """
    parser = FileParser()
    return parser.parse(file_path, file_type)
