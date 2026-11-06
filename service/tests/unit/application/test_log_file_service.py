"""LogFileService（日志文件浏览）单元测试。"""

import pytest

from src.application.services.log_file_service import LogFileNotFoundError, LogFileService


@pytest.fixture
def logs_dir(tmp_path):
    """构造含典型日志产物的临时日志目录。"""
    (tmp_path / "app.log").write_text("line1\nline2\n" + "\n".join(f"app-{i}" for i in range(300)), encoding="utf-8")
    (tmp_path / "error.log").write_text("boom\n", encoding="utf-8")
    (tmp_path / "app.2026-11-05_10-00-00_123456.log.zip").write_bytes(b"PK\x03\x04")
    (tmp_path / "backend_stdout.log").write_text("stdout\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    # 显式错开 mtime（秒级字符串排序在同秒创建时不稳定）
    import os

    os.utime(tmp_path / "app.log", (1000, 1000))
    os.utime(tmp_path / "app.2026-11-05_10-00-00_123456.log.zip", (2000, 2000))
    os.utime(tmp_path / "backend_stdout.log", (3000, 3000))
    os.utime(tmp_path / "error.log", (4000, 4000))
    return tmp_path


@pytest.fixture
def service(logs_dir):
    return LogFileService(logs_dir=logs_dir)


@pytest.mark.unit
class TestListFiles:
    async def test_lists_only_regular_files_sorted_by_mtime(self, service, logs_dir):
        files = await service.list_files()

        names = [f.name for f in files]
        assert set(names) == {"app.log", "error.log", "app.2026-11-05_10-00-00_123456.log.zip", "backend_stdout.log"}
        # 子目录不出现
        assert "sub" not in names
        # 倒序：最后写入的 error.log 在前（同秒内按排序稳定性不苛求）
        assert files[0].name == "error.log"
        assert all(f.sizeBytes > 0 for f in files)

    async def test_missing_dir_returns_empty(self, tmp_path):
        svc = LogFileService(logs_dir=tmp_path / "nope")
        assert await svc.list_files() == []


@pytest.mark.unit
class TestTail:
    async def test_tail_returns_last_lines(self, service):
        content = await service.tail("app.log", lines=10)
        lines = content.splitlines()
        assert len(lines) == 10
        assert lines[-1].startswith("app-299")
        assert lines[0].startswith("app-290")

    async def test_tail_more_lines_than_file(self, service):
        content = await service.tail("error.log", lines=100)
        assert content == "boom"

    async def test_tail_lines_capped_at_limit(self, service):
        content = await service.tail("app.log", lines=999999)
        assert len(content.splitlines()) <= 1000

    async def test_tail_multibyte_utf8_safe(self, logs_dir, service):
        (logs_dir / "cn.log").write_text("第一行\n第二行\n", encoding="utf-8")
        content = await service.tail("cn.log", lines=10)
        assert content.splitlines() == ["第一行", "第二行"]


@pytest.mark.unit
class TestPathSafety:
    async def test_rejects_path_traversal(self, service, tmp_path):
        """穿越逃逸必须被拒绝（绝对路径解析 + 目录包含校验双保险）。"""
        secret = tmp_path.parent / "secret.txt"
        secret.write_text("top secret", encoding="utf-8")
        with pytest.raises(ValueError):
            await service.open_path("../secret.txt")

    async def test_rejects_illegal_characters(self, service):
        with pytest.raises(ValueError):
            await service.open_path("app.log/../../etc/passwd")
        with pytest.raises(ValueError):
            await service.open_path("..")

    async def test_rejects_missing_file(self, service):
        with pytest.raises(LogFileNotFoundError):
            await service.open_path("not-exist.log")

    async def test_open_path_returns_resolved_file(self, service, logs_dir):
        path = await service.open_path("app.log")
        assert path == (logs_dir / "app.log").resolve()
