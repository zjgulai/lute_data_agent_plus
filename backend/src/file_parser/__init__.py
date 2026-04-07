"""文件解析模块.

提供 PDF / Word / Excel 文件的文本提取功能。
"""

from .engine import FileParseError, FileParser, parse_file

__all__ = [
    "FileParser",
    "FileParseError",
    "parse_file",
]
