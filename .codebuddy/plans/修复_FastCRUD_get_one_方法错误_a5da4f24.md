---
name: 修复 FastCRUD get_one 方法错误
overview: 将所有仓库文件中错误的 get_one 方法调用替换为正确的 get 方法
todos:
  - id: fix-user-repo
    content: 修复 user_repository.py 中的 get_one 方法调用
    status: completed
  - id: fix-role-repo
    content: 修复 role_repository.py 中的 get_one 方法调用
    status: completed
  - id: fix-permission-repo
    content: 修复 permission_repository.py 中的 get_one 方法调用
    status: completed
  - id: fix-department-repo
    content: 修复 department_repository.py 中的 get_one 方法调用
    status: completed
---

## 用户需求

修复登录接口抛出的 AttributeError: 'FastCRUD' object has no attribute 'get_one' 错误

## 问题分析

FastCRUD >= 0.15.0 版本中不存在 `get_one` 方法，正确的方法是使用 `get` 方法。`get` 方法支持通过任意字段作为关键字参数进行查询单条记录。

## 受影响文件

- `user_repository.py` - 第42、53行
- `role_repository.py` - 第47、58行
- `permission_repository.py` - 第46行
- `department_repository.py` - 第54行

## 技术方案

将所有仓库实现中的 `get_one` 方法调用替换为 `get` 方法。FastCRUD 的 `get` 方法支持通过关键字参数按字段查询，签名完全兼容。

## 修改内容

将 `self._crud.get_one(self.session, field=value)` 统一改为 `self._crud.get(self.session, field=value)`

## 目录结构

```
service/src/infrastructure/repositories/
├── user_repository.py        # [MODIFY] 第42、53行
├── role_repository.py        # [MODIFY] 第47、58行
├── permission_repository.py  # [MODIFY] 第46行
└── department_repository.py  # [MODIFY] 第54行
```