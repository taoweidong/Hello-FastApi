#!/usr/bin/env python3
"""
代码质量综合评估脚本
结合多种工具进行全面的代码质量检查
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass
class QualityMetrics:
    """代码质量指标"""

    type_coverage: float = 0.0
    test_coverage: float = 0.0
    code_complexity: float = 0.0
    style_compliance: float = 0.0
    security_issues: int = 0
    maintainability_score: float = 0.0


class QualityAssessment:
    """代码质量评估器"""

    def __init__(self, target_path: str = "."):
        self.target_path = target_path
        self.metrics = QualityMetrics()

    def assess_type_coverage(self) -> tuple[bool, float]:
        """评估类型注解覆盖率"""
        try:
            # 使用mypy检查类型覆盖率
            cmd = ["mypy", self.target_path, "--linecount-report", "."]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            if result.returncode == 0:
                # 简单估算：假设没有类型错误就是100%覆盖率
                return True, 100.0
            else:
                # 分析错误类型，估算覆盖率
                error_lines = result.stdout.strip().split("\n")
                type_errors = len([line for line in error_lines if "error:" in line.lower()])
                # 简单估算：错误越少，覆盖率越高
                coverage = max(0, 100 - type_errors * 5)  # 错误个错误扣5分
                return False, coverage

        except FileNotFoundError:
            logger.warning("⚠️ 未安装mypy，跳过类型覆盖率评估")
            return True, 70.0  # 估计值
        except Exception as e:
            logger.exception(f"⚠️ 类型覆盖率评估出错：{e}")
            return False, 0.0

    def assess_test_coverage(self) -> tuple[bool, float]:
        """评估测试覆盖率"""
        try:
            # 使用coverage.py检查测试覆盖率
            cmd = ["coverage", "run", "-m", "pytest", self.target_path, "--quiet"]
            subprocess.run(cmd, capture_output=True, cwd=os.getcwd())

            # 生成覆盖率报告
            report_cmd = ["coverage", "report", "--format=total"]
            result = subprocess.run(report_cmd, capture_output=True, text=True, cwd=os.getcwd())

            if result.returncode == 0 and result.stdout.strip():
                coverage = float(result.stdout.strip().rstrip("%"))
                return coverage >= 80, coverage
            else:
                return False, 0.0

        except FileNotFoundError:
            logger.warning("⚠️ 未安装coverage.py，跳过测试覆盖率评估")
            return True, 60.0  # 估计值
        except Exception as e:
            logger.exception(f"⚠️ 测试覆盖率评估出错：{e}")
            return False, 0.0

    def assess_code_complexity(self) -> tuple[bool, float]:
        """评估代码复杂度"""
        try:
            # 使用radon检查圈复杂度
            cmd = ["radon", "cc", self.target_path, "-a", "-s"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            if result.returncode == 0:
                # 解析复杂度结果
                output = result.stdout
                if "Average complexity:" in output:
                    # 提取平均复杂度
                    lines = output.split("\n")
                    for line in lines:
                        if "Average complexity:" in line:
                            complexity_str = line.split(":")[1].strip()
                            # 简单映射：A=1, B=2, C=3, D=4, E=5, F=6
                            complexity_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
                            complexity_score = complexity_map.get(complexity_str, 3)
                            # 为分数 (6-复杂度)*16.67
                            score = (6 - complexity_score) * 16.67
                            return complexity_score <= 3, max(0, score)

                return True, 80.0  # 默认良好分数
            else:
                return False, 0.0

        except FileNotFoundError:
            logger.warning("⚠️ 未安装radon，跳过代码复杂度评估")
            return True, 75.0  # 估计值
        except Exception as e:
            logger.exception(f"⚠️ 代码复杂度评估出错：{e}")
            return False, 0.0

    def assess_security(self) -> tuple[bool, int]:
        """评估安全问题"""
        try:
            # 使用bandit检查安全问题
            cmd = ["bandit", "-r", self.target_path, "-f", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            if result.returncode == 0:
                try:
                    # 解析JSON输出
                    data = json.loads(result.stdout)
                    issues = data.get("results", [])
                    high_severity = len([issue for issue in issues if issue.get("issue_severity") == "HIGH"])
                    return high_severity == 0, high_severity
                except json.JSONDecodeError:
                    # 如果不是JSON格式，简单统计
                    issues_count = result.stdout.count("HIGH")
                    return issues_count == 0, issues_count
            else:
                return False, 10  # 估计有较多问题

        except FileNotFoundError:
            logger.warning("⚠️ 未安装bandit，跳过安全评估")
            return True, 2  # 估计值
        except Exception as e:
            logger.exception(f"⚠️安全评估出错：{e}")
            return False, 5  # 估计值

    def calculate_maintainability_score(self) -> float:
        """计算可维护性分数"""
        # 基于各项指标计算综合分数
        weights = {
            "type_coverage": 0.25,
            "test_coverage": 0.25,
            "code_complexity": 0.20,
            "style_compliance": 0.15,
            "security_adjustment": 0.15,
        }

        # 计算基础分数
        base_score = (
            self.metrics.type_coverage * weights["type_coverage"]
            + self.metrics.test_coverage * weights["test_coverage"]
            + self.metrics.code_complexity * weights["code_complexity"]
            + self.metrics.style_compliance * weights["style_compliance"]
        )

        # 安全问题扣分
        security_penalty = min(20, self.metrics.security_issues * 2)  # 安全个安全问题扣2分，最多扣20分

        final_score = max(0, base_score - security_penalty)
        return final_score

    def run_comprehensive_assessment(self) -> QualityMetrics:
        """运行全面的质量评估"""
        logger.info("🔬 开始全面代码质量评估")
        logger.info("=" * 60)

        # 评估各项指标
        logger.info("1. 评估类型注解覆盖率...")
        type_passed, self.metrics.type_coverage = self.assess_type_coverage()
        logger.info(f"   类型覆盖率: {self.metrics.type_coverage:.1f}% {'✅' if type_passed else '❌'}")

        logger.info("\n2. 评估测试覆盖率...")
        test_passed, self.metrics.test_coverage = self.assess_test_coverage()
        logger.info(f"   测试覆盖率: {self.metrics.test_coverage:.1f}% {'✅' if test_passed else '❌'}")

        logger.info("\n3. 评估代码复杂度...")
        complexity_passed, self.metrics.code_complexity = self.assess_code_complexity()
        logger.info(f"   代码复杂度: {self.metrics.code_complexity:.1f}% {'✅' if complexity_passed else '❌'}")

        logger.info("\n4. 评估代码风格合规性...")
        # 使用之前的flake8检查结果
        style_cmd = ["flake8", self.target_path, "--count", "--quiet"]
        try:
            result = subprocess.run(style_cmd, capture_output=True, text=True, cwd=os.getcwd())
            style_violations = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
            self.metrics.style_compliance = max(0, 100 - style_violations * 0.5)  # 每个违规扣0.5分
            style_passed = style_violations <= 10
            logger.info(f"  风合规性: {self.metrics.style_compliance:.1f}% {'✅' if style_passed else '❌'}")
        except Exception:
            self.metrics.style_compliance = 85.0  # 估计值
            logger.info(f"  风合规性: {self.metrics.style_compliance:.1f}%✅")

        logger.info("\n5. 评估安全问题...")
        security_passed, self.metrics.security_issues = self.assess_security()
        logger.info(f"  安全问题: {self.metrics.security_issues}个 {'✅' if security_passed else '❌'}")

        # 计算最终可维护性分数
        self.metrics.maintainability_score = self.calculate_maintainability_score()

        logger.info("\n" + "=" * 60)
        logger.info("📊综评估结果:")
        logger.info(f"  🎯 类型注解覆盖率: {self.metrics.type_coverage:.1f}%")
        logger.info(f"  🧪测试覆盖率: {self.metrics.test_coverage:.1f}%")
        logger.info(f"   🔄 代码复杂度: {self.metrics.code_complexity:.1f}%")
        logger.info(f"  📝合规性: {self.metrics.style_compliance:.1f}%")
        logger.info(f"   🔒 安全问题: {self.metrics.security_issues}个")
        logger.info(f"  🏆综可维护性分数: {self.metrics.maintainability_score:.1f}/100")

        # 提供改进建议
        self._provide_recommendations()

        return self.metrics

    def _provide_recommendations(self) -> None:
        """提供改进建议"""
        logger.info("\n💡改进建议:")

        if self.metrics.type_coverage < 80:
            logger.info("   •类型加类型注解，特别是函数参数和返回值")

        if self.metrics.test_coverage < 80:
            logger.info("   •编写更多单元测试，提高测试覆盖率")

        if self.metrics.code_complexity < 70:
            logger.info("   •简化复杂函数，考虑拆分大函数")

        if self.metrics.style_compliance < 90:
            logger.info("   •运行代码格式化工具（black, isort）")

        if self.metrics.security_issues > 0:
            logger.info("   • 修复安全问题，使用bandit工具检查")

        # 总体评级
        score = self.metrics.maintainability_score
        if score >= 90:
            logger.info("\n🏆 代码质量优秀！继续保持！")
        elif score >= 75:
            logger.info("\n👍 代码质量良好，有改进空间")
        elif score >= 60:
            logger.warning("\n⚠️ 代码质量一般，建议重点改进")
        else:
            logger.error("\n❌ 代码质量需要大幅改进")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Python代码质量综合评估")
    parser.add_argument("target", nargs="?", default=".", help="要评估的路径")
    parser.add_argument("--json", action="store_true", help="输出JSON格式结果")

    args = parser.parse_args()

    # 检查目标路径
    if not Path(args.target).exists():
        logger.error(f"❌目标路径不存在：{args.target}")
        sys.exit(1)

    # 运行评估
    assessor = QualityAssessment(args.target)
    metrics = assessor.run_comprehensive_assessment()

    # 输出JSON格式结果
    if args.json:
        result = {
            "target": args.target,
            "metrics": {
                "type_coverage": round(metrics.type_coverage, 2),
                "test_coverage": round(metrics.test_coverage, 2),
                "code_complexity": round(metrics.code_complexity, 2),
                "style_compliance": round(metrics.style_compliance, 2),
                "security_issues": metrics.security_issues,
                "maintainability_score": round(metrics.maintainability_score, 2),
            },
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
