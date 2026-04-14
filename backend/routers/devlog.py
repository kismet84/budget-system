"""
开发日志 REST API

数据来源：Hermes SQLite (~/.hermes/hermes_state.db)
该数据库由 Hermes Agent 管理，前端只读。
"""
import sqlite3
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.security import get_current_user

router = APIRouter(prefix="/devlog", tags=["开发日志"])

# ── Hermes SQLite 路径 ────────────────────────────────────────────────────────
# Hermes Agent 默认使用 ~/.hermes/state.db
_HERMES_HOME = Path.home() / ".hermes"
_HERMES_DB = _HERMES_HOME / "state.db"


def _get_conn() -> sqlite3.Connection:
    if not _HERMES_DB.exists():
        raise HTTPException(status_code=503, detail="Hermes 数据库不存在")
    conn = sqlite3.connect(str(_HERMES_DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    # 解析 JSON 字段（None 值也要处理）
    raw_tags = d.get("tags")
    if raw_tags is not None:
        try:
            d["tags"] = json.loads(raw_tags) if isinstance(raw_tags, str) else raw_tags
        except (json.JSONDecodeError, TypeError):
            d["tags"] = []
    else:
        d["tags"] = []
    d["needs_summary"] = bool(d.get("needs_summary"))
    return d


# ── Schemas ────────────────────────────────────────────────────────────────────

class DevLogEntry(BaseModel):
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    type: str
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    author: str
    source: str
    file_path: Optional[str] = None
    project: str
    commit_hash: Optional[str] = None
    quality: int
    created_at: float
    needs_summary: bool


class DevLogListResponse(BaseModel):
    total: int
    entries: List[DevLogEntry]


class DevLogSearchResponse(BaseModel):
    total: int
    entries: List[DevLogEntry]


# ── 路由 ───────────────────────────────────────────────────────────────────────

@router.get("/", response_model=DevLogListResponse)
def list_devlogs(
    project: str = "budget-system",
    dev_type: Optional[str] = Query(None, description="类型过滤：feature/bugfix/optimization/refactor/change/commit"),
    source: Optional[str] = Query(None, description="来源过滤：file/agent/session/git"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """分页列出开发日志"""
    conn = _get_conn()
    try:
        sql = "SELECT * FROM devlogs WHERE project = ?"
        params: list = [project]
        if dev_type:
            sql += " AND type = ?"
            params.append(dev_type)
        if source:
            sql += " AND source = ?"
            params.append(source)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        total = conn.execute(
            "SELECT COUNT(*) FROM devlogs WHERE project = ?", (project,)
        ).fetchone()[0]
        rows = conn.execute(sql, params).fetchall()
        entries = [_row_to_dict(r) for r in rows]
        return DevLogListResponse(total=total, entries=entries)
    finally:
        conn.close()


@router.get("/search", response_model=DevLogSearchResponse)
def search_devlogs(
    q: str = Query(..., description="搜索关键词"),
    project: str = "budget-system",
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """全文搜索开发日志（使用 FTS5）"""
    conn = _get_conn()
    try:
        # FTS5 search
        rows = conn.execute(
            """SELECT d.* FROM devlogs d
               JOIN devlogs_fts f ON d.rowid = f.rowid
               WHERE devlogs_fts MATCH ? AND d.project = ?
               ORDER BY rank LIMIT ?""",
            (q, project, limit),
        ).fetchall()
        total = len(rows)
        entries = [_row_to_dict(r) for r in rows]
        return DevLogSearchResponse(total=total, entries=entries)
    finally:
        conn.close()


@router.get("/types", response_model=List[str])
def list_types(current_user: dict = Depends(get_current_user)):
    """列出所有 entry type"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT type FROM devlogs ORDER BY type"
        ).fetchall()
        return [r["type"] for r in rows]
    finally:
        conn.close()


@router.get("/sources", response_model=List[str])
def list_sources(current_user: dict = Depends(get_current_user)):
    """列出所有 entry source"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT source FROM devlogs ORDER BY source"
        ).fetchall()
        return [r["source"] for r in rows]
    finally:
        conn.close()


@router.get("/tags", response_model=List[str])
def list_tags(project: str = "budget-system", current_user: dict = Depends(get_current_user)):
    """列出所有标签（去重）"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT tags FROM devlogs WHERE project = ? AND tags IS NOT NULL",
            (project,),
        ).fetchall()
        tags_set = set()
        for row in rows:
            try:
                tags_set.update(json.loads(row["tags"]))
            except (json.JSONDecodeError, TypeError):
                pass
        return sorted(tags_set)
    finally:
        conn.close()


@router.get("/stats")
def devlog_stats(project: str = "budget-system", current_user: dict = Depends(get_current_user)):
    """获取统计数据：每日数量、按类型分布、按来源分布"""
    conn = _get_conn()
    try:
        # Total count
        total = conn.execute(
            "SELECT COUNT(*) FROM devlogs WHERE project = ?", (project,)
        ).fetchone()[0]

        # By type
        by_type = {}
        for row in conn.execute(
            "SELECT type, COUNT(*) as c FROM devlogs WHERE project = ? GROUP BY type",
            (project,),
        ).fetchall():
            by_type[row["type"]] = row["c"]

        # By source
        by_source = {}
        for row in conn.execute(
            "SELECT source, COUNT(*) as c FROM devlogs WHERE project = ? GROUP BY source",
            (project,),
        ).fetchall():
            by_source[row["source"]] = row["c"]

        # Daily count (last 30 days)
        daily = []
        for row in conn.execute(
            """SELECT date(created_at, 'unixepoch') as day, COUNT(*) as c
               FROM devlogs
               WHERE project = ? AND created_at > strftime('%s', 'now', '-30 days')
               GROUP BY day ORDER BY day DESC""",
            (project,),
        ).fetchall():
            daily.append({"date": row["day"], "count": row["c"]})

        return {
            "total": total,
            "by_type": by_type,
            "by_source": by_source,
            "daily": daily,
        }
    finally:
        conn.close()


@router.get("/{devlog_id}", response_model=DevLogEntry)
def get_devlog(devlog_id: str, current_user: dict = Depends(get_current_user)):
    """获取单条开发日志详情"""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM devlogs WHERE id = ?", (devlog_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="DevLog not found")
        return _row_to_dict(row)
    finally:
        conn.close()
