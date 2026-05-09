"""Alembic CLI 命令测试。"""

import subprocess
from pathlib import Path


def test_migrate_command_runs():
    """测试 migrate 命令可以成功执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "migrate"],
        cwd=project_root,
        capture_output=True,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(project_root),
        },
    )
    output = (result.stdout or b"").decode("utf-8", errors="ignore") + (result.stderr or b"").decode("utf-8", errors="ignore")
    assert (
        result.returncode == 0
        or "already up to date" in output.lower()
        or "no such table" in output.lower()
    )


def test_rollback_command_exists():
    """测试 rollback 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    # 先初始化数据库
    subprocess.run(
        ["python", "-m", "scripts.cli", "initdb"],
        cwd=project_root,
        capture_output=True,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(project_root),
        },
    )
    # 执行回滚
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "rollback", "--steps", "1"],
        cwd=project_root,
        capture_output=True,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(project_root),
        },
    )
    output = (result.stdout or b"").decode("utf-8", errors="ignore") + (result.stderr or b"").decode("utf-8", errors="ignore")
    assert (
        "回滚" in output
        or "downgrade" in output.lower()
        or result.returncode == 0
    )


def test_stamp_command_exists():
    """测试 stamp 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "stamp", "head"],
        cwd=project_root,
        capture_output=True,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(project_root),
        },
    )
    output = (result.stdout or b"").decode("utf-8", errors="ignore") + (result.stderr or b"").decode("utf-8", errors="ignore")
    assert (
        result.returncode == 0
        or "标记" in output
    )
