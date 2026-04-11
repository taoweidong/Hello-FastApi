---
name: pre-commit-ruff-check
description: 在 Git 提交前自动执行 Ruff 格式化和代码规范检查，确保所有 Python 代码符合项目规范。当用户准备提交代码、执行 git commit 前、或提到代码检查和格式化时使用此技能。
---

# 提交前 Ruff 检查

## 功能说明

在每次编码任务结束后、Git 提交代码前，自动执行 Ruff 格式化和规范检查并修复问题，确保所有代码满足规范要求和格式化要求。

## 执行流程

### 第一步：检查代码状态

```bash
# 查看当前变更状态
git status
```

### 第二步：执行 Ruff 格式化

```bash
# 进入 service 目录
cd service

# 执行格式化（自动修复格式问题）
ruff format src/ tests/

# 检查格式化结果
ruff format --check src/ tests/
```

### 第三步：执行 Ruff 规范检查

```bash
# 执行 lint 检查并自动修复可修复的问题
ruff check src/ tests/ --fix

# 检查是否还有未修复的问题
ruff check src/ tests/
```

### 第四步：处理检查结果

**如果检查和格式化都通过：**
- 继续提交流程

**如果还有未修复的问题：**
- 查看错误报告
- 手动修复无法自动修复的问题
- 重新执行检查，直到全部通过

### 第五步：添加并提交代码

```bash
# 返回项目根目录
cd ..

# 添加所有变更
git add -A

# 提交代码（使用有意义的提交信息）
git commit -m "你的提交信息"

# 推送到远程仓库
git push
```

## 注意事项

1. **必须在 service 目录下执行 Ruff 命令**
2. **先格式化，再检查** - 格式化可能会修复一些 lint 问题
3. **自动修复优先** - 使用 `--fix` 参数让 Ruff 自动修复问题
4. **手动处理残留问题** - 对于无法自动修复的问题，需要手动修改代码
5. **确保全部通过再提交** - 只有所有检查和格式化都通过后才能提交

## 完整命令序列

```bash
# 1. 进入 service 目录
cd service

# 2. 格式化代码
ruff format src/ tests/

# 3. 规范检查并自动修复
ruff check src/ tests/ --fix

# 4. 验证是否全部通过
ruff format --check src/ tests/
ruff check src/ tests/

# 5. 返回根目录并提交
cd ..
git add -A
git commit -m "feat: 你的提交信息"
git push
```

## 常见问题

### Q: 如果 Ruff 检查失败怎么办？
A: 查看错误输出，优先使用 `--fix` 自动修复。对于无法自动修复的问题（如逻辑错误、命名问题），需要手动修改代码。

### Q: 格式化后代码被改动了，需要重新添加吗？
A: 是的，格式化会修改文件，需要重新 `git add -A` 添加变更。

### Q: 可以跳过某些文件吗？
A: 可以在 `pyproject.toml` 的 `[tool.ruff]` 配置中使用 `exclude` 参数排除特定文件或目录。

## 项目配置参考

当前项目的 Ruff 配置在 `service/pyproject.toml` 中：

- `line-length = 320` - 最大行长度
- `skip-magic-trailing-comma = true` - 不因尾随逗号强制换行
- 函数参数在不超过 320 字符时保持单行，超过时自动换行
