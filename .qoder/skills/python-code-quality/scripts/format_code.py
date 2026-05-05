#!/usr/bin/env python3
"""
代码格式化脚本
使用black和isort自动格式化Python代码
"""

import os
import subprocess
import sys
from pathlib import Path

from loguru import logger


def run_black_format(target_path: str = ".", check_only: bool = False) -> bool:
    """
    使用black格式化代码

    Args:
        target_path:格化的目标路径
        check_only: 是否只检查不修改

    Returns:
        bool:格化是否成功
    """
    cmd = ["black"]

    if check_only:
        cmd.append("--check")

    cmd.extend(["--line-length", "88", "--target-version", "py39", "--skip-string-normalization", target_path])

    try:
        logger.info(f"⚫正在使用black格式化 {target_path}...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            if check_only:
                logger.success("✅ 代码格式符合black标准")
            else:
                logger.success("✅ 代码格式化完成")
            return True
        else:
            if check_only:
                logger.error("❌ 代码格式不符合black标准")
                logger.error(result.stdout)
            else:
                logger.error("❌ 代码格式化失败")
                logger.error(result.stderr)
            return False

    except FileNotFoundError:
        logger.error("❌ 未找到black，请先安装：pip install black")
        return False
    except Exception as e:
        logger.exception(f"❌ black格式化出错：{e}")
        return False


def run_isort_imports(target_path: str = ".", check_only: bool = False) -> bool:
    """
    使用isort整理导入语句

    Args:
        target_path:整理导入的目标路径
        check_only: 是否只检查不修改

    Returns:
        bool:导入整理是否成功
    """
    cmd = ["isort"]

    if check_only:
        cmd.append("--check-only")

    cmd.extend(
        [
            "--profile",
            "black",
            "--multi-line",
            "3",
            "--trailing-comma",
            "--force-grid-wrap",
            "0",
            "--use-parentheses",
            "--ensure-newline-before-comments",
            target_path,
        ]
    )

    try:
        logger.info(f"🔄正在使用isort整理 {target_path} 的导入语句...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            if check_only:
                logger.success("✅导入语句整理符合isort标准")
            else:
                logger.success("✅导入语句整理完成")
            return True
        else:
            if check_only:
                logger.error("❌导入语句整理不符合isort标准")
                logger.error(result.stdout)
            else:
                logger.error("❌导入语句整理失败")
                logger.error(result.stderr)
            return False

    except FileNotFoundError:
        logger.error("❌ 未找到isort，请先安装：pip install isort")
        return False
    except Exception as e:
        logger.exception(f"❌isort导入整理出错：{e}")
        return False


def run_flake8_check(target_path: str = ".") -> tuple[bool, list[str]]:
    """
    使用flake8检查代码风格

    Args:
        target_path:的检查的目标路径

    Returns:
        Tuple[bool, List[str]]: (检查是否通过,错误信息列表)
    """
    cmd = [
        "flake8",
        target_path,
        "--max-line-length=88",
        "--extend-ignore=E203,W503",
        "--exclude=.git,__pycache__,docs,build,dist",
    ]

    try:
        logger.info(f"📝正在使用flake8检查 {target_path} 的代码风格...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            logger.success("✅代码风格符合flake8标准")
            return True, []
        else:
            errors = result.stdout.strip().split("\n") if result.stdout.strip() else []
            logger.error("❌发现代码风格问题：")
            for error in errors[:10]:  # 只显示前10个错误
                logger.error(f"  {error}")
            if len(errors) > 10:
                logger.error(f"  ... 还有 {len(errors) - 10} 个问题")
            return False, errors

    except FileNotFoundError:
        logger.warning("⚠️  未找到flake8，跳过代码风格检查")
        return True, []
    except Exception as e:
        logger.exception(f"❌ flake8检查出错：{e}")
        return False, [str(e)]


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Python代码格式化工具")
    parser.add_argument("target", nargs="?", default=".", help="要处理的路径")
    parser.add_argument("--check", action="store_true", help="只检查，不修改文件")
    parser.add_argument("--skip-imports", action="store_true", help="跳过导入语句整理")
    parser.add_argument("--skip-format", action="store_true", help="跳过代码格式化")
    parser.add_argument("--skip-lint", action="store_true", help="跳过代码检查")

    args = parser.parse_args()

    target_path = args.target

    # 检查目标路径是否存在
    if not Path(target_path).exists():
        logger.error(f"❌目路径不存在：{target_path}")
        sys.exit(1)

    logger.info("🎨 开始Python代码格式化")
    logger.info("=" * 50)

    success_count = 0
    total_checks = 0

    # 整理导入语句
    if not args.skip_imports:
        total_checks += 1
        if run_isort_imports(target_path, args.check):
            success_count += 1
        logger.info("")

    # 代码格式化
    if not args.skip_format:
        total_checks += 1
        if run_black_format(target_path, args.check):
            success_count += 1
        logger.info("")

    # 代码风格检查
    if not args.skip_lint and not args.check:
        total_checks += 1
        lint_passed, _ = run_flake8_check(target_path)
        if lint_passed:
            success_count += 1
        logger.info("")

    logger.info("=" * 50)

    if success_count == total_checks:
        if args.check:
            logger.success("🎉 所有检查都通过了！代码格式良好")
        else:
            logger.success("🎉 代码格式化和检查完成！")
        sys.exit(0)
    else:
        logger.warning(f"🔧 请修复 {total_checks - success_count} 个问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
