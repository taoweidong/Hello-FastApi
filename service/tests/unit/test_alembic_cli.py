"""Alembic CLI 命令测试。

.. warning::
    本文件的测试通过子进程**真实执行** ``alembic`` 命令（upgrade/downgrade/stamp），
    因此必须经 ``_cli_env()`` 把数据库指向 ``tmp_path`` 下的临时文件。

    历史事故（2026-10-25 修复）：早期版本未做隔离，子进程继承了 pytest 的
    ``APP_ENV=testing``，而 ``alembic/env.py`` 当时用裸 ``Settings()`` 取
    DATABASE_URL——testing 的库地址覆盖只存在于 ``get_settings()`` 中，裸构造器
    静默落到模型默认值 ``sql/dev.db``。结果每次跑 pytest 都对**开发库**执行
    ``downgrade -1`` + ``stamp head``：``sys_userloginlog.username`` 列被删，
    版本戳却被推回 head，形成「版本戳超前、结构落后」的 schema 漂移，
    进而导致 E2E 的登录日志接口 500。修复同时包含两侧：
    ``alembic/env.py`` 改用 ``get_settings()``；本文件加临时库隔离。
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _cli_env(tmp_path: Path) -> dict[str, str]:
    """构造子进程环境：把数据库指向临时文件，绝不碰 dev.db / test.db。

    选 ``APP_ENV=development`` 而非 ``testing``：testing 的 DATABASE_URL 覆盖
    是以构造参数形式传入 ``Settings(...)`` 的（优先级高于环境变量），会盖掉
    这里的临时地址；development 的覆盖字典为空，环境变量即可生效
    （pydantic-settings 优先级：构造参数 > 环境变量 > dotenv > 模型默认值）。
    """
    db_file = tmp_path / "cli_test.db"
    return {
        **os.environ,
        "PYTHONPATH": str(PROJECT_ROOT),
        "APP_ENV": "development",
        "DATABASE_URL": f"sqlite+aiosqlite:///{db_file.as_posix()}",
    }


def _run_cli(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
    """执行 ``python -m scripts.cli <args>`` 并捕获输出。"""
    return subprocess.run(
        [sys.executable, "-m", "scripts.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        env=env,
    )


def _output(result: subprocess.CompletedProcess[bytes]) -> str:
    """合并 stdout/stderr 为文本（容忍 Windows 下的编码噪声）。"""
    return ((result.stdout or b"") + (result.stderr or b"")).decode("utf-8", errors="ignore")


def test_migrate_command_runs(tmp_path: Path) -> None:
    """migrate（upgrade head）可在全新数据库上成功执行，且重复执行幂等。"""
    env = _cli_env(tmp_path)
    result = _run_cli(["migrate"], env)
    assert result.returncode == 0, _output(result)

    # 幂等：已在 head 时再次升级不应报错
    again = _run_cli(["migrate"], env)
    assert again.returncode == 0, _output(again)


def test_rollback_command_exists(tmp_path: Path) -> None:
    """rollback（downgrade）可回滚一步，且回滚后能重新升级到 head。

    序列：migrate 建 schema 与版本表 → rollback -1 → migrate 恢复。
    早期版本先跑 initdb（create_all，无 alembic_version）再 downgrade，
    在没有版本表的库上回滚必然失败；这里先用 migrate 保证前提成立。
    """
    env = _cli_env(tmp_path)
    assert _run_cli(["migrate"], env).returncode == 0

    result = _run_cli(["rollback", "--steps", "1"], env)
    output = _output(result)
    assert result.returncode == 0, output
    assert "回滚" in output or "downgrade" in output.lower()

    # 回滚后库仍可升级到 head（验证 downgrade 没有破坏 schema）
    restored = _run_cli(["migrate"], env)
    assert restored.returncode == 0, _output(restored)


def test_stamp_command_exists(tmp_path: Path) -> None:
    """stamp 可标记数据库版本（不执行 SQL）。"""
    env = _cli_env(tmp_path)
    assert _run_cli(["migrate"], env).returncode == 0

    result = _run_cli(["stamp", "head"], env)
    assert result.returncode == 0, _output(result)
