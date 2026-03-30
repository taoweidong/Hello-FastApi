"""System API - 系统管理和监控路由模块。

提供部门管理、在线用户、登录日志、操作日志、系统日志等接口。
"""

import random

from fastapi import APIRouter, Body, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import list_response, success_response
from src.api.dependencies import get_current_active_user
from src.application.dto.department_dto import DepartmentCreateDTO, DepartmentListQueryDTO, DepartmentUpdateDTO
from src.application.dto.log_dto import (
    BatchDeleteLogDTO,
    LoginLogListQueryDTO,
    OperationLogListQueryDTO,
    SystemLogListQueryDTO,
)
from src.application.services.department_service import DepartmentService
from src.application.services.log_service import LogService
from src.infrastructure.database import get_db

system_extra_router = APIRouter()


# =============================================================================
# 部门管理
# =============================================================================


@system_extra_router.post("/dept")
async def get_dept_list(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取部门列表（扁平结构）。
    
    前端调用: POST /api/system/dept
    返回扁平列表格式，前端自动转为树形结构。
    """
    # 构建查询参数
    query = DepartmentListQueryDTO(
        name=data.get("name"),
        status=data.get("status"),
    )

    service = DepartmentService(db)
    departments = await service.get_departments(query)

    # 转换为前端期望的格式
    dept_list = []
    for dept in departments:
        dept_dict = {
            "id": dept.id,
            "parentId": 0 if not dept.parent_id else dept.parent_id,
            "name": dept.name,
            "sort": dept.sort,
            "principal": dept.principal or "",
            "phone": dept.phone or "",
            "email": dept.email or "",
            "status": dept.status,
            "remark": dept.remark or "",
            "createTime": int(dept.created_at.timestamp() * 1000) if dept.created_at else None,
        }
        dept_list.append(dept_dict)

    return success_response(data=dept_list)


@system_extra_router.post("/dept/create")
async def create_department(
    dto: DepartmentCreateDTO,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建部门。
    
    前端调用: POST /api/system/dept/create
    """
    service = DepartmentService(db)
    department = await service.create_department(dto)
    return success_response(
        data={
            "id": department.id,
            "name": department.name,
        },
        message="创建成功",
        code=201,
    )


@system_extra_router.put("/dept/{dept_id}")
async def update_department(
    dept_id: str,
    dto: DepartmentUpdateDTO,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新部门。
    
    前端调用: PUT /api/system/dept/{id}
    """
    service = DepartmentService(db)
    department = await service.update_department(dept_id, dto)
    return success_response(
        data={
            "id": department.id,
            "name": department.name,
        },
        message="更新成功",
    )


@system_extra_router.delete("/dept/{dept_id}")
async def delete_department(
    dept_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除部门。
    
    前端调用: DELETE /api/system/dept/{id}
    """
    service = DepartmentService(db)
    await service.delete_department(dept_id)
    return success_response(message="删除成功")


# =============================================================================
# 在线用户（stub 实现，需要会话管理机制）
# =============================================================================


@system_extra_router.post("/online-logs")
async def get_online_logs(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user)
):
    """获取在线用户列表（stub 数据）。
    
    注意：在线用户管理需要会话管理机制（如 Redis），
    目前返回 stub 数据，后续可实现真实的会话管理。
    """
    list_data = [
        {"id": 1, "username": "admin", "ip": "192.168.1.1", "address": "中国河南省信阳市", "system": "macOS", "browser": "Chrome", "loginTime": "2026-03-29T10:00:00"},
        {"id": 2, "username": "common", "ip": "192.168.1.2", "address": "中国广东省深圳市", "system": "Windows", "browser": "Firefox", "loginTime": "2026-03-29T09:30:00"}
    ]
    # 支持按 username 筛选
    username = data.get("username", "")
    if username:
        list_data = [item for item in list_data if username in item["username"]]
    return success_response(data={"list": list_data, "total": len(list_data), "pageSize": 10, "currentPage": 1})


# =============================================================================
# 登录日志
# =============================================================================


@system_extra_router.post("/login-logs")
async def get_login_logs(
    query: LoginLogListQueryDTO = Body(default={}),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取登录日志列表。
    
    前端调用: POST /api/system/login-logs
    响应格式: { list, total, pageSize, currentPage }
    """
    service = LogService(db)
    logs, total = await service.get_login_logs(query)

    # 转换为前端期望的格式
    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "username": log.username,
            "ip": log.ip or "",
            "address": log.address or "",
            "system": log.system or "",
            "browser": log.browser or "",
            "status": log.status,
            "behavior": log.behavior or "",
            "loginTime": log.login_time.isoformat() if log.login_time else None,
        })

    return list_response(
        list_data=log_list,
        total=total,
        page_size=query.pageSize,
        current_page=query.pageNum,
    )


@system_extra_router.post("/login-logs/batch-delete")
async def batch_delete_login_logs(
    dto: BatchDeleteLogDTO,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除登录日志。
    
    前端调用: POST /api/system/login-logs/batch-delete
    """
    service = LogService(db)
    count = await service.delete_login_logs(dto)
    return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")


@system_extra_router.post("/login-logs/clear")
async def clear_login_logs(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """清空所有登录日志。
    
    前端调用: POST /api/system/login-logs/clear
    """
    service = LogService(db)
    count = await service.clear_login_logs()
    return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")


# =============================================================================
# 操作日志
# =============================================================================


@system_extra_router.post("/operation-logs")
async def get_operation_logs(
    query: OperationLogListQueryDTO = Body(default={}),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取操作日志列表。
    
    前端调用: POST /api/system/operation-logs
    响应格式: { list, total, pageSize, currentPage }
    """
    service = LogService(db)
    logs, total = await service.get_operation_logs(query)

    # 转换为前端期望的格式
    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "username": log.username,
            "ip": log.ip or "",
            "address": log.address or "",
            "system": log.system or "",
            "browser": log.browser or "",
            "status": log.status,
            "summary": log.summary or "",
            "module": log.module or "",
            "operatingTime": log.operating_time.isoformat() if log.operating_time else None,
        })

    return list_response(
        list_data=log_list,
        total=total,
        page_size=query.pageSize,
        current_page=query.pageNum,
    )


@system_extra_router.post("/operation-logs/batch-delete")
async def batch_delete_operation_logs(
    dto: BatchDeleteLogDTO,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除操作日志。
    
    前端调用: POST /api/system/operation-logs/batch-delete
    """
    service = LogService(db)
    count = await service.delete_operation_logs(dto)
    return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")


@system_extra_router.post("/operation-logs/clear")
async def clear_operation_logs(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """清空所有操作日志。
    
    前端调用: POST /api/system/operation-logs/clear
    """
    service = LogService(db)
    count = await service.clear_operation_logs()
    return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")


# =============================================================================
# 系统日志
# =============================================================================


@system_extra_router.post("/system-logs")
async def get_system_logs(
    query: SystemLogListQueryDTO = Body(default={}),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取系统日志列表。
    
    前端调用: POST /api/system/system-logs
    响应格式: { list, total, pageSize, currentPage }
    """
    service = LogService(db)
    logs, total = await service.get_system_logs(query)

    # 转换为前端期望的格式
    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "level": log.level or "",
            "module": log.module or "",
            "url": log.url or "",
            "method": log.method or "",
            "ip": log.ip or "",
            "address": log.address or "",
            "system": log.system or "",
            "browser": log.browser or "",
            "takesTime": log.takes_time,
            "requestTime": log.request_time.isoformat() if log.request_time else None,
        })

    return list_response(
        list_data=log_list,
        total=total,
        page_size=query.pageSize,
        current_page=query.pageNum,
    )


@system_extra_router.post("/system-logs-detail")
async def get_system_logs_detail(
    data: dict = Body(default={}),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取系统日志详情。
    
    前端调用: POST /api/system/system-logs-detail
    请求体: { id: "xxx" }
    """
    log_id = data.get("id")
    if not log_id:
        return success_response(data=None, message="日志ID不能为空")

    service = LogService(db)
    detail = await service.get_system_log_detail(log_id)

    return success_response(data=detail)


@system_extra_router.post("/system-logs/batch-delete")
async def batch_delete_system_logs(
    dto: BatchDeleteLogDTO,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除系统日志。
    
    前端调用: POST /api/system/system-logs/batch-delete
    """
    service = LogService(db)
    count = await service.delete_system_logs(dto)
    return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")


@system_extra_router.post("/system-logs/clear")
async def clear_system_logs(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """清空所有系统日志。
    
    前端调用: POST /api/system/system-logs/clear
    """
    service = LogService(db)
    count = await service.clear_system_logs()
    return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")


# =============================================================================
# 地图数据接口（stub 数据）
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
# 卡片列表接口（stub 数据）
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
