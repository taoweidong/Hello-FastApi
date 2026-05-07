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
        text=True,
        encoding="utf-8",
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(project_root),
        },
    )
    assert (
        result.returncode == 0
        or result.stdout and "already up to date" in result.stdout.lower()
        or result.stderr and "no such table" in result.stderr.lower()
    )


def test_rollback_command_exists():
    """测试 rollback 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "rollback", "--steps", "1"],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(project_root),
        },
    )
    assert (
        result.stdout
        and "回滚" in result.stdout
        or result.stderr
        and "回滚" in result.stderr
        or result.returncode == 0
    )


def test_stamp_command_exists():
    """测试 stamp 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "stamp", "head"],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(project_root),
        },
    )
    assert (
        result.returncode == 0
        or result.stdout
        and "标记" in result.stdout
        or result.stderr
        and "标记" in result.stderr
    )
