---
name: 修复 FastCRUD 返回类型问题
overview: 在所有仓库的 get 方法调用中添加 return_as_model=True 参数，使其返回模型对象而不是字典
todos:
  - id: fix-user-repo-return-type
    content: 修复 user_repository.py 中所有 get 方法调用，添加 return_as_model=True
    status: completed
  - id: fix-role-repo-return-type
    content: 修复 role_repository.py 中所有 get 方法调用，添加 return_as_model=True
    status: completed
  - id: fix-permission-repo-return-type
    content: 修复 permission_repository.py 中所有 get 方法调用，添加 return_as_model=True
    status: completed
  - id: fix-department-repo-return-type
    content: 修复 department_repository.py 中所有 get 方法调用，添加 return_as_model=True
    status: completed
---

## 用户需求

修复登录接口抛出的 AttributeError: 'dict' object has no attribute 'hashed_password' 错误

## 问题分析

FastCRUD 的 `get` 方法默认返回字典类型，而整个服务层代码都期望仓库方法返回模型对象以便访问属性。需要在所有仓库的查询方法中添加 `return_as_model=True` 参数。

## 受影响文件

- `user_repository.py` - 3个方法需要修改
- `role_repository.py` - 3个方法需要修改
- `permission_repository.py` - 2个方法需要修改
- `department_repository.py` - 2个方法需要修改

## 技术方案

在所有仓库实现中的 `self._crud.get()` 调用添加 `return_as_model=True` 参数，使 FastCRUD 返回 SQLModel 模型对象而非字典。

## 修改示例

```python
# 修改前
return await self._crud.get(self.session, username=username)

# 修改后
return await self._crud.get(self.session, username=username, return_as_model=True)
```

## 目录结构

```
service/src/infrastructure/repositories/
├── user_repository.py        # [MODIFY] get_by_id, get_by_username, get_by_email 方法
├── role_repository.py        # [MODIFY] get_by_id, get_by_name, get_by_code 方法
├── permission_repository.py  # [MODIFY] get_by_id, get_by_code 方法
└── department_repository.py  # [MODIFY] get_by_id, get_by_name 方法
```