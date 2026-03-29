"""System API - 系统管理和监控 stub 路由模块。

提供部门管理、在线用户、登录日志、操作日志、系统日志等接口的 stub 实现。
当前返回示例数据，后续可接入真实数据源。
"""

from fastapi import APIRouter, Body, Depends
from typing import Any
import random

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


# =============================================================================
# 地图数据接口
# =============================================================================

@system_extra_router.get("/get-map-info")
async def get_map_info(
    current_user: dict = Depends(get_current_active_user)
):
    """获取地图数据（stub 数据）。

    前端调用: GET /api/system/get-map-info
    返回模拟的车辆位置数据，用于地图展示。
    """
    # 生成模拟地图数据
    map_list = []
    drivers = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]

    for i in range(50):
        # 生成河南省范围内的随机坐标
        lng = round(random.uniform(113.0, 114.1), 4)
        lat = round(random.uniform(34.0, 35.1), 4)
        # 生成随机车牌号
        plate_number = f"豫A{random.randint(10000, 99999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"

        map_list.append({
            "plateNumber": plate_number,
            "driver": random.choice(drivers),
            "orientation": random.randint(1, 360),
            "lng": lng,
            "lat": lat
        })

    return success_response(data=map_list)


# =============================================================================
# 卡片列表接口
# =============================================================================

@system_extra_router.post("/get-card-list")
async def get_card_list(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取卡片列表（stub 数据）。

    前端调用: POST /api/system/get-card-list
    返回模拟的卡片数据，用于列表展示。
    """
    # 模拟卡片数据
    card_names = ["SSL证书", "人脸识别", "CVM", "云数据库", "T-Sec 云防火墙"]
    banners = [
        "https://tdesign.gtimg.com/tdesign-pro/cloud-server.jpg",
        "https://tdesign.gtimg.com/tdesign-pro/t-sec.jpg",
        "https://tdesign.gtimg.com/tdesign-pro/ssl.jpg",
        "https://tdesign.gtimg.com/tdesign-pro/cloud-db.jpg",
        "https://tdesign.gtimg.com/tdesign-pro/face-recognition.jpg"
    ]
    descriptions = [
        "SSL证书又叫服务器证书，腾讯云为您提供证书的一站式服务，包括免费、付费证书的申请、管理及部署",
        "基于腾讯优图强大的面部分析技术，提供包括人脸检测与分析、五官定位、人脸搜索、人脸比对、人脸验证等功能",
        "云硬盘为您提供用于CVM的持久性数据块级存储服务。云硬盘中的数据自动地在可用区内以多副本冗余",
        "云数据库MySQL为用户提供安全可靠，性能卓越、易于维护的企业级云数据库服务",
        "腾讯安全云防火墙产品，是腾讯云安全团队结合云原生的优势，自主研发的SaaS化防火墙产品"
    ]

    card_list = []
    for i in range(1, 49):
        card_list.append({
            "index": i,
            "isSetup": random.choice([True, False]),
            "type": random.randint(1, 5),
            "banner": random.choice(banners),
            "name": random.choice(card_names),
            "description": random.choice(descriptions)
        })

    return success_response(data={"list": card_list})
