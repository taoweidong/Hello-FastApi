#!/usr/bin/env python3
"""
Python代码质量工具安装脚本
"""

import subprocess
import sys

from loguru import logger


def install_package(package: str, description: str = "") -> bool:
    """安装Python包"""
    try:
        logger.info(f"📦正在安装 {package} {description}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True, text=True)
        if result.returncode == 0:
            logger.success(f"✅ {package}安装成功")
            return True
        else:
            logger.error(f"❌ {package} 安装失败: {result.stderr}")
            return False
    except Exception as e:
        logger.exception(f"❌安装 {package} 时出错: {e}")
        return False


def main():
    """主安装函数"""
    logger.info("🔧 Python代码质量工具安装器")
    logger.info("=" * 50)

    # 核心必需工具
    core_packages = [
        ("mypy", "类型检查器"),
        ("black", "代码格式化工具"),
        ("isort", "导入语句整理工具"),
        ("flake8", "代码风格检查器"),
    ]

    # 可选高级工具
    optional_packages = [
        ("coverage", "测试覆盖率工具"),
        ("pytest", "测试框架"),
        ("bandit", "安全检查工具"),
        ("radon", "代码复杂度分析工具"),
        ("unimport", "未使用导入检查工具"),
    ]

    logger.info("1. 安装核心工具...")
    core_success = 0
    for package, desc in core_packages:
        if install_package(package, f"({desc})"):
            core_success += 1

    logger.info(f"\n✅ 核心工具安装完成 ({core_success}/{len(core_packages)})")

    # 询问是否安装可选工具
    logger.info("\n2.可选高级工具:")
    for package, desc in optional_packages:
        logger.info(f"   - {package}: {desc}")

    choice = input("\n是否安装可选工具？(y/N): ").strip().lower()
    if choice in ["y", "yes"]:
        optional_success = 0
        for package, desc in optional_packages:
            if install_package(package, f"({desc})"):
                optional_success += 1
        logger.info(f"\n✅ 可选工具安装完成 ({optional_success}/{len(optional_packages)})")

    logger.info("\n" + "=" * 50)
    if core_success == len(core_packages):
        logger.success("🎉所有核心工具安装成功！")
        logger.info("\n现在可以使用以下命令:")
        logger.info("  python scripts/type_check.py src/     # 类型检查")
        logger.info("  python scripts/format_code.py src/    # 代码格式化")
        logger.info("  python scripts/quality_check.py src/  #综质量评估")
    else:
        logger.warning("⚠️ 部分工具安装失败，请手动安装缺失的工具")


if __name__ == "__main__":
    main()
