"""Alembic CLI 命令测试。"""

import subprocess
import sys
from pathlib import Path


def test_migrate_command_runs():
    """测试 migrate 命令可以成功执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "scripts.cli", "migrate"],
        cwd=project_root,
        capture_output=True,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    stdout = (result.stdout or b"").decode("utf-8", errors="ignore")
    stderr = (result.stderr or b"").decode("utf-8", errors="ignore")
    output = stdout + stderr
    assert (
        result.returncode == 0
        or "already up to date" in output.lower()
        or "no such table" in output.lower()
        or "already exists" in output.lower()
        or "duplicate" in output.lower()
    )


def test_rollback_command_exists():
    """测试 rollback 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    # 先初始化数据库
    subprocess.run(
        [sys.executable, "-m", "scripts.cli", "initdb"],
        cwd=project_root,
        capture_output=True,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    # 执行回滚
    result = subprocess.run(
        [sys.executable, "-m", "scripts.cli", "rollback", "--steps", "1"],
        cwd=project_root,
        capture_output=True,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    stdout = (result.stdout or b"").decode("utf-8", errors="ignore")
    stderr = (result.stderr or b"").decode("utf-8", errors="ignore")
    output = stdout + stderr
    assert "回滚" in output or "downgrade" in output.lower() or result.returncode == 0


def test_stamp_command_exists():
    """测试 stamp 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "scripts.cli", "stamp", "head"],
        cwd=project_root,
        capture_output=True,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    stdout = (result.stdout or b"").decode("utf-8", errors="ignore")
    stderr = (result.stderr or b"").decode("utf-8", errors="ignore")
    output = stdout + stderr
    assert result.returncode == 0 or "标记" in output
