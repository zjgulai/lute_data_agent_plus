"""数据服务模块：Excel 读取与数据切片."""

from .excel_reader import ExcelDataReader, DataReadingError
from .data_slicer import DataSlicer, SliceConfiguration

__all__ = [
    "ExcelDataReader",
    "DataReadingError",
    "DataSlicer",
    "SliceConfiguration",
]
