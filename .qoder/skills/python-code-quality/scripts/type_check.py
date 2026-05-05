#!/usr/bin/env python3
"""
类型检查脚本
使用mypy检查Python代码的类型注解
"""

import os
import subprocess
import sys
from pathlib import Path

from loguru import logger


def run_mypy_check(target_path: str = ".", strict: bool = True) -> bool:
    """
    运行mypy类型检查

     Args:
         target_path:的检查的目录或文件路径
         strict: 是否使用严格模式

     Returns:
         bool: 检查是否通过
    """
    # 构建mypy命令
    cmd = ["mypy", target_path]

    if strict:
        cmd.extend(
            [
                "--strict",
                "--disallow-untyped-defs",
                "--disallow-incomplete-defs",
                "--check-untyped-defs",
                "--disallow-untyped-decorators",
            ]
        )

    # 添加额外的配置选项
    cmd.extend(
        [
            "--show-error-codes",
            "--show-error-context",
            "--pretty",
            "--no-error-summary",  # 减冗余输出
        ]
    )

    try:
        logger.info(f"🔍正在检查 {target_path} 的类型注解...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            logger.info("✅ 类型检查通过！")
            if result.stdout.strip():
                logger.info(result.stdout)
            return True
        else:
            logger.error("❌ 类型检查发现问题：")
            logger.error(result.stdout)
            if result.stderr:
                logger.error("错误信息：")
                logger.error(result.stderr)
            return False

    except FileNotFoundError:
        logger.error("❌ 未找到mypy，请先安装：pip install mypy")
        return False
    except Exception as e:
        logger.exception(f"❌检查过程中出现错误：{e}")
        return False


def check_imports(target_path: str) -> list[str]:
    """
    检查未使用的导入

     Args:
         target_path:的检查的路径

     Returns:
         List[str]: 未使用导入的列表
    """
    unused_imports = []

    try:
        # 使用unimport检查未使用的导入
        cmd = ["unimport", "--check", "--diff", target_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0 and result.stdout:
            unused_imports = result.stdout.strip().split("\n")

    except FileNotFoundError:
        logger.warning("⚠️  未安装unimport，跳过未使用导入检查")
    except Exception as e:
        logger.exception(f"⚠️ 导入检查出错：{e}")

    return unused_imports


def main():
    """主函数"""
    # 检查是否有帮助参数
    if "--help" in sys.argv or "-h" in sys.argv:
        logger.info("Python类型检查工具")
        logger.info("用法: python type_check.py [路径] [选项]")
        logger.info("选项:")
        logger.info("  --help, -h    显示帮助信息")
        logger.info("           的目录或文件路径（默认当前目录)")
        return

    # 参数解析
    target = "."
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        target = sys.argv[1]

    logger.info("🚀 开始Python代码质量检查")
    logger.info("=" * 50)

    # 检查目标路径是否存在
    if not Path(target).exists():
        logger.error(f"❌目标路径不存在：{target}")
        sys.exit(1)

    # 运行类型检查
    type_check_passed = run_mypy_check(target)

    # 检查未使用的导入
    unused_imports = check_imports(target)
    if unused_imports:
        logger.warning(f"\n⚠️  发现 {len(unused_imports)} 个未使用的导入：")
        for imp in unused_imports[:10]:  # 只显示前10个
            logger.warning(f"  - {imp}")
        if len(unused_imports) > 10:
            logger.warning(f"  ... 还有 {len(unused_imports) - 10} 个")

    logger.info("\n" + "=" * 50)

    if type_check_passed and not unused_imports:
        logger.success("🎉 所有检查都通过了！代码质量良好")
        sys.exit(0)
    else:
        logger.warning("🔧建修复上述问题以提高代码质量")
        sys.exit(1)


if __name__ == "__main__":
    main()
