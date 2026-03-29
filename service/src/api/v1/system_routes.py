"""System API - 系统管理和监控 stub 路由模块。

提供部门管理、在线用户、登录日志、操作日志、系统日志等接口的 stub 实现。
当前返回示例数据，后续可接入真实数据源。
"""

from fastapi import APIRouter, Body, Depends
from typing import Any

from src.api.common import success_response
from src.api.dependencies import get_current_active_user

system_extra_router = APIRouter()


@system_extra_router.post("/dept")
async def get_dept_list(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取部门管理列表（stub 数据）"""
    dept_list = [
        {"name": "杭州总公司", "parentId": 0, "id": 100, "sort": 0, "phone": "15888888888", "principal": "张三", "email": "admin@example.com", "status": 1, "type": 1, "createTime": 1605456000000, "remark": "总部"},
        {"name": "郑州分公司", "parentId": 100, "id": 101, "sort": 1, "phone": "15888888888", "principal": "李四", "email": "zz@example.com", "status": 1, "type": 2, "createTime": 1605456000000, "remark": ""},
        {"name": "研发部门", "parentId": 101, "id": 103, "sort": 1, "phone": "15888888888", "principal": "王五", "email": "dev@example.com", "status": 1, "type": 3, "createTime": 1605456000000, "remark": ""},
        {"name": "市场部门", "parentId": 102, "id": 108, "sort": 1, "phone": "15888888888", "principal": "赵六", "email": "market@example.com", "status": 1, "type": 3, "createTime": 1605456000000, "remark": ""},
        {"name": "深圳分公司", "parentId": 100, "id": 102, "sort": 2, "phone": "15888888888", "principal": "孙七", "email": "sz@example.com", "status": 1, "type": 2, "createTime": 1605456000000, "remark": ""},
        {"name": "市场部门", "parentId": 101, "id": 104, "sort": 2, "phone": "15888888888", "principal": "周八", "email": "market2@example.com", "status": 1, "type": 3, "createTime": 1605456000000, "remark": ""},
        {"name": "财务部门", "parentId": 102, "id": 109, "sort": 2, "phone": "15888888888", "principal": "吴九", "email": "finance@example.com", "status": 1, "type": 3, "createTime": 1605456000000, "remark": ""},
        {"name": "测试部门", "parentId": 101, "id": 105, "sort": 3, "phone": "15888888888", "principal": "郑十", "email": "test@example.com", "status": 0, "type": 3, "createTime": 1605456000000, "remark": ""},
        {"name": "财务部门", "parentId": 101, "id": 106, "sort": 4, "phone": "15888888888", "principal": "王十一", "email": "finance2@example.com", "status": 1, "type": 3, "createTime": 1605456000000, "remark": ""},
        {"name": "运维部门", "parentId": 101, "id": 107, "sort": 5, "phone": "15888888888", "principal": "陈十二", "email": "ops@example.com", "status": 0, "type": 3, "createTime": 1605456000000, "remark": ""}
    ]
    return success_response(data=dept_list)


@system_extra_router.post("/online-logs")
async def get_online_logs(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取在线用户列表（stub 数据）"""
    list_data = [
        {"id": 1, "username": "admin", "ip": "192.168.1.1", "address": "中国河南省信阳市", "system": "macOS", "browser": "Chrome", "loginTime": "2026-03-29T10:00:00"},
        {"id": 2, "username": "common", "ip": "192.168.1.2", "address": "中国广东省深圳市", "system": "Windows", "browser": "Firefox", "loginTime": "2026-03-29T09:30:00"}
    ]
    # 支持按 username 筛选
    username = data.get("username", "")
    if username:
        list_data = [item for item in list_data if username in item["username"]]
    return success_response(data={"list": list_data, "total": len(list_data), "pageSize": 10, "currentPage": 1})


@system_extra_router.post("/login-logs")
async def get_login_logs(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取登录日志列表（stub 数据）"""
    list_data = [
        {"id": 1, "username": "admin", "ip": "192.168.1.1", "address": "中国河南省信阳市", "system": "macOS", "browser": "Chrome", "status": 1, "behavior": "账号登录", "loginTime": "2026-03-29T10:00:00"},
        {"id": 2, "username": "common", "ip": "192.168.1.2", "address": "中国广东省深圳市", "system": "Windows", "browser": "Firefox", "status": 0, "behavior": "第三方登录", "loginTime": "2026-03-29T09:30:00"}
    ]
    username = data.get("username", "")
    if username:
        list_data = [item for item in list_data if username in item["username"]]
    return success_response(data={"list": list_data, "total": len(list_data), "pageSize": 10, "currentPage": 1})


@system_extra_router.post("/operation-logs")
async def get_operation_logs(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取操作日志列表（stub 数据）"""
    list_data = [
        {"id": 1, "username": "admin", "ip": "192.168.1.1", "address": "中国河南省信阳市", "system": "macOS", "browser": "Chrome", "status": 1, "summary": "菜单管理-添加菜单", "module": "系统管理", "operatingTime": "2026-03-29T10:00:00"},
        {"id": 2, "username": "common", "ip": "192.168.1.2", "address": "中国广东省深圳市", "system": "Windows", "browser": "Firefox", "status": 0, "summary": "列表分页查询", "module": "在线用户", "operatingTime": "2026-03-29T09:30:00"}
    ]
    module_filter = data.get("module", "")
    if module_filter:
        list_data = [item for item in list_data if module_filter in item["module"]]
    return success_response(data={"list": list_data, "total": len(list_data), "pageSize": 10, "currentPage": 1})


@system_extra_router.post("/system-logs")
async def get_system_logs(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取系统日志列表（stub 数据）"""
    list_data = [
        {"id": 1, "level": 1, "module": "菜单管理", "url": "/menu", "method": "post", "ip": "192.168.1.1", "address": "中国河南省信阳市", "system": "macOS", "browser": "Chrome", "takesTime": 10, "requestTime": "2026-03-29T10:00:00"},
        {"id": 2, "level": 0, "module": "地图", "url": "/get-map-info", "method": "get", "ip": "192.168.1.2", "address": "中国广东省深圳市", "system": "Windows", "browser": "Firefox", "takesTime": 1200, "requestTime": "2026-03-29T09:30:00"}
    ]
    module_filter = data.get("module", "")
    if module_filter:
        list_data = [item for item in list_data if module_filter in item["module"]]
    return success_response(data={"list": list_data, "total": len(list_data), "pageSize": 10, "currentPage": 1})


@system_extra_router.post("/system-logs-detail")
async def get_system_logs_detail(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取系统日志详情（stub 数据）"""
    log_id = data.get("id", 1)
    detail = {
        "id": log_id,
        "level": 1,
        "module": "菜单管理",
        "url": "/menu",
        "method": "post",
        "ip": "192.168.1.1",
        "address": "中国河南省信阳市",
        "system": "macOS",
        "browser": "Chrome",
        "takesTime": 10,
        "requestTime": "2026-03-29T10:00:00",
        "responseHeaders": {"Content-Type": "application/json"},
        "responseBody": {"code": 0, "message": "操作成功", "data": []},
        "requestHeaders": {"Accept": "application/json", "Authorization": "Bearer token"},
        "requestBody": {},
        "traceId": "1495502411171032"
    }
    return success_response(data=detail)
