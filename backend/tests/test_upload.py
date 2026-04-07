"""文件上传与解析测试.

验证上传 API、文件解析器和大小限制。
"""

from __future__ import annotations

import os
import tempfile

import pytest

from api.session import _orchestrators as session_orchestrators
from api.upload import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, _validate_file
from file_parser import FileParseError, parse_file
from file_parser.engine import FileParser
from llm import LLMOrchestrator
from state_machine import AnalysisMode


class TestFileParser:
    """测试文件解析引擎."""

    def test_parse_unsupported_type(self):
        with pytest.raises(FileParseError, match="不支持的文件类型"):
            parse_file("test.txt", "txt")

    def test_parse_pdf(self):
        # 创建一个空白的 PyPDF2 可读文件
        from PyPDF2 import PdfWriter
        import io

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(buffer.read())
            path = f.name

        try:
            parser = FileParser()
            result = parser.parse(path, "pdf")
            assert isinstance(result, str)
        finally:
            os.remove(path)

    def test_parse_word(self):
        from docx import Document

        doc = Document()
        doc.add_paragraph("Hello World")
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
            doc.save(path)

        try:
            result = parse_file(path, "docx")
            assert "Hello World" in result
        finally:
            os.remove(path)

    def test_parse_excel(self):
        import pandas as pd

        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = f.name
            df.to_excel(path, index=False)

        try:
            result = parse_file(path, "xlsx")
            assert "A" in result
            assert "x" in result
        finally:
            os.remove(path)


class TestUploadValidation:
    """测试上传校验逻辑."""

    def test_allowed_extension(self):
        class FakeFile:
            filename = "report.pdf"

        # 不应抛出异常
        _validate_file(FakeFile())

    def test_disallowed_extension(self):
        class FakeFile:
            filename = "virus.exe"

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _validate_file(FakeFile())
        assert exc_info.value.status_code == 400


class TestUploadAPI:
    """测试上传 API（使用内存中的 orchestrator）."""

    @pytest.fixture(autouse=True)
    def setup(self):
        session_orchestrators.clear()
        orch = LLMOrchestrator(session_id="test-upload-session")
        orch.state_machine.start(mode=AnalysisMode.AUTO)
        session_orchestrators["test-upload-session"] = orch
        yield
        session_orchestrators.clear()

    async def _upload(self, session_id, file_mock):
        from api.upload import upload_file
        return await upload_file(session_id, file_mock)

    def test_upload_pdf_success(self):
        import asyncio
        from fastapi import UploadFile
        import io
        from PyPDF2 import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        pdf_buffer = io.BytesIO()
        writer.write(pdf_buffer)
        pdf_buffer.seek(0)

        upload_file_mock = UploadFile(filename="test.pdf", file=pdf_buffer)
        result = asyncio.run(self._upload("test-upload-session", upload_file_mock))
        assert result["success"] is True
        assert result["file_type"] == "pdf"
        assert result["parse_status"] == "success"

    def test_upload_excel_success(self):
        import asyncio
        from fastapi import UploadFile
        import io
        import pandas as pd

        df = pd.DataFrame({"区域": ["美国", "中国"], "GMV": [100, 200]})
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        upload_file_mock = UploadFile(filename="test.xlsx", file=excel_buffer)
        result = asyncio.run(self._upload("test-upload-session", upload_file_mock))
        assert result["success"] is True
        assert result["file_type"] == "xlsx"
        assert result["parse_status"] == "success"

    def test_upload_size_limit(self):
        import asyncio
        from fastapi import UploadFile
        import io

        large_content = b"x" * (MAX_FILE_SIZE + 1)
        file_mock = UploadFile(filename="large.pdf", file=io.BytesIO(large_content))

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(self._upload("test-upload-session", file_mock))
        assert exc_info.value.status_code == 413

    def test_upload_session_not_found(self):
        import asyncio
        from fastapi import UploadFile
        import io

        file_mock = UploadFile(filename="test.pdf", file=io.BytesIO(b"content"))
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(self._upload("nonexistent", file_mock))
        assert exc_info.value.status_code == 404

    def test_list_files(self):
        from api.upload import list_files
        files = list_files("test-upload-session")
        assert files["session_id"] == "test-upload-session"
        assert isinstance(files["files"], list)

    def test_delete_file(self):
        from api.upload import delete_file
        orch = session_orchestrators["test-upload-session"]
        orch.state_machine.set_context("uploaded_files", [
            {"file_id": "f1", "file_path": "/tmp/f1.pdf", "original_name": "f1.pdf", "file_type": "pdf", "file_size": 10, "parse_status": "success"}
        ])
        result = delete_file("test-upload-session", "f1")
        assert result["success"] is True
        remaining = orch.state_machine.get_context("uploaded_files") or []
        assert len(remaining) == 0
