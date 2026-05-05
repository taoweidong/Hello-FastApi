# Python代码质量技能

这个技能帮助您编写高质量的Python代码，重点关注面向对象编程和类型注解的使用。

##功能特性

- ✨ **面向对象编程指导** - 提供类设计最佳实践
-📝 **类型注解规范** - 详细的类型注解使用指南
-🔍 **自动代码检查** -多种代码质量工具
-🎨 **自动代码格式化** - 保持代码风格一致性
- 📊 **质量评估报告** -综代码质量评分

##包含的工具脚本

### 1. 类型检查脚本 (`scripts/type_check.py`)

使用mypy检查代码的类型注解：

```bash
#检查当前目录
python scripts/type_check.py

#检查特定文件或目录
python scripts/type_check.py src/

#只不修改
python scripts/type_check.py --check
```

### 2. 代码格式化脚本 (`scripts/format_code.py`)

使用black和isort自动格式化代码：

```bash
#格化当前目录
python scripts/format_code.py

#格化特定目录
python scripts/format_code.py src/

#只检查格式（不修改文件）
python scripts/format_code.py --check

#跳过特定检查
python scripts/format_code.py --skip-imports --skip-lint
```

### 3.评估脚本 (`scripts/quality_check.py`)

综合评估代码质量：

```bash
# 评估当前目录
python scripts/quality_check.py

# 评估特定目录
python scripts/quality_check.py src/

# 输出JSON格式结果
python scripts/quality_check.py --json
```

##安依赖

###方法一：使用安装脚本（推荐）

```bash
#运行自动安装脚本
python scripts/install_tools.py
```

###方法二：手动安装

```bash
#核心依赖
pip install mypy black isort flake8

#可选的高级工具
pip install coverage pytest bandit radon unimport
```

###方法三：使用requirements.txt

创建`requirements-quality.txt`文件：

```txt
#核心工具
mypy>=1.0.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0

#可选工具
coverage>=7.0.0
pytest>=7.0.0
bandit>=1.7.0
radon>=6.0.0
unimport>=0.16.0
```

## 使用示例

###快质量检查工作流

```bash
# 1.检查先检查类型注解
python scripts/type_check.py src/

# 2.格化代码
python scripts/format_code.py src/

# 3.综质量评估
python scripts/quality_check.py src/
```

###集成到开发流程

在您的开发环境中添加这些检查：

```bash
# Git pre-commit hook示例
#!/bin/bash
python .qoder/skills/python-code-quality/scripts/type_check.py src/
if [ $? -ne 0 ]; then
    echo "类型检查失败，请修复后再提交"
    exit 1
fi

python .qoder/skills/python-code-quality/scripts/format_code.py src/ --check
if [ $? -ne 0 ]; then
    echo "代码格式不符合标准，请运行格式化脚本"
    exit 1
fi
```

## 代码质量标准

### 优秀代码的标准

- ✅ 类型注解覆盖率 ≥ 90%
- ✅测试覆盖率 ≥ 80%
-✅ 代码复杂度 ≤ 3 (Radon评级A-B)
-✅ 代码风格合规性 ≥ 95%
- ✅ 无高危安全问题

###面对象设计原则

1. **单一职责原则** -类只负责一个功能
2. **开闭原则** - 对扩展开放，对修改关闭
3. **里氏替换原则** -子类可以替换父类
4. **接口隔离原则** - 使用多个专门接口而非一个通用接口
5. **依赖倒置原则** - 依赖抽象而非具体实现

##常问题

### Q: 如何处理遗留代码的类型注解？
A:可以逐步添加类型注解，优先处理公共接口和复杂函数。

### Q: 类型检查太严格怎么办？
A: 可以使用 `# type: ignore` 注释忽略特定行，但要谨慎使用。

### Q: 如何配置检查规则？
A:可以在项目根目录创建配置文件如 `mypy.ini`、`pyproject.toml`等。

##贡

欢迎提出改进建议和贡献代码！