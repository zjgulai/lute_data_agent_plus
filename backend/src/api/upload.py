"""文件上传与解析 API.

提供外部文件上传、解析状态查询和删除功能。
"""

from __future__ import annotations

import os
import shutil
import uuid
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.session import _orchestrators
from file_parser import FileParseError, parse_file

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

# 上传文件存储根目录
UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "xls"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _get_upload_dir(session_id: str) -> str:
    """获取会话上传目录."""
    upload_dir = os.path.join(UPLOAD_ROOT, session_id)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写）."""
    return os.path.splitext(filename)[1].lower().lstrip(".")


def _validate_file(file: UploadFile) -> None:
    """校验文件类型和大小."""
    ext = _get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}",
        )


@router.post("/{session_id}")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """上传外部文件并进行解析.

    限制 20MB，支持 pdf / docx / xlsx / xls。
    """
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    _validate_file(file)

    # 读取内容并校验大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过 20MB 限制")

    # 生成唯一文件名
    file_id = f"file-{uuid.uuid4().hex[:8]}"
    ext = _get_file_extension(file.filename or "")
    safe_name = f"{file_id}.{ext}"
    upload_dir = _get_upload_dir(session_id)
    file_path = os.path.join(upload_dir, safe_name)

    # 保存文件
    with open(file_path, "wb") as f:
        f.write(content)

    # 解析文件
    parse_status = "pending"
    parsed_content = ""
    try:
        parsed_content = parse_file(file_path, ext)
        parse_status = "success"
    except FileParseError as e:
        parse_status = "error"
        parsed_content = str(e)

    # 构建文件记录
    file_record = {
        "file_id": file_id,
        "original_name": file.filename,
        "file_type": ext,
        "file_size": len(content),
        "file_path": file_path,
        "parse_status": parse_status,
        "parsed_content": parsed_content,
    }

    # 存入 orchestrator context
    uploaded_files = orchestrator.state_machine.get_context("uploaded_files") or []
    uploaded_files.append(file_record)
    orchestrator.state_machine.set_context("uploaded_files", uploaded_files)

    return {
        "success": True,
        "file_id": file_id,
        "original_name": file.filename,
        "file_type": ext,
        "file_size": len(content),
        "parse_status": parse_status,
    }


@router.get("/{session_id}/files")
def list_files(session_id: str) -> dict[str, Any]:
    """获取会话已上传文件列表."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    uploaded_files = orchestrator.state_machine.get_context("uploaded_files") or []
    files = [
        {
            "file_id": f["file_id"],
            "original_name": f["original_name"],
            "file_type": f["file_type"],
            "file_size": f["file_size"],
            "parse_status": f["parse_status"],
        }
        for f in uploaded_files
    ]

    return {"session_id": session_id, "files": files}


@router.delete("/{session_id}/{file_id}")
def delete_file(session_id: str, file_id: str) -> dict[str, Any]:
    """删除已上传文件."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    uploaded_files = orchestrator.state_machine.get_context("uploaded_files") or []
    target = None
    new_files = []
    for f in uploaded_files:
        if f["file_id"] == file_id:
            target = f
        else:
            new_files.append(f)

    if not target:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 删除物理文件
    try:
        if os.path.exists(target["file_path"]):
            os.remove(target["file_path"])
    except OSError:
        pass

    orchestrator.state_machine.set_context("uploaded_files", new_files)

    return {"success": True, "file_id": file_id}


@router.delete("/{session_id}")
def clear_files(session_id: str) -> dict[str, Any]:
    """清空会话所有上传文件."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    uploaded_files = orchestrator.state_machine.get_context("uploaded_files") or []
    for f in uploaded_files:
        try:
            if os.path.exists(f["file_path"]):
                os.remove(f["file_path"])
        except OSError:
            pass

    orchestrator.state_machine.set_context("uploaded_files", [])

    # 尝试删除空目录
    upload_dir = os.path.join(UPLOAD_ROOT, session_id)
    try:
        if os.path.isdir(upload_dir):
            shutil.rmtree(upload_dir)
    except OSError:
        pass

    return {"success": True, "session_id": session_id}
