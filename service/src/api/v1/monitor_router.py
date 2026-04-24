"""系统监控路由模块。

提供在线用户、地图数据、卡片列表等 stub 接口。
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

import random
from typing import Any

from classy_fastapi import Routable, get, post
from fastapi import Body, Depends

from src.api.common import success_response
from src.api.dependencies import require_permission


class MonitorRouter(Routable):
    """系统监控路由类，提供在线用户、地图数据、卡片列表等 stub 接口。"""

    @post("/online-logs")
    async def get_online_logs(
        self, data: dict = Body(default={}), _: dict = Depends(require_permission("monitor:view"))
    ) -> dict:
        """获取在线用户列表（stub 数据）。"""
        list_data: list[dict[str, Any]] = [
            {
                "id": 1,
                "username": "admin",
                "ip": "192.168.1.1",
                "address": "中国河南省信阳市",
                "system": "macOS",
                "browser": "Chrome",
                "loginTime": "2026-03-29T10:00:00",
            },
            {
                "id": 2,
                "username": "common",
                "ip": "192.168.1.2",
                "address": "中国广东省深圳市",
                "system": "Windows",
                "browser": "Firefox",
                "loginTime": "2026-03-29T09:30:00",
            },
        ]
        username = data.get("username", "")
        if username:
            list_data = [item for item in list_data if username in item["username"]]
        return success_response(data={"list": list_data, "total": len(list_data), "pageSize": 10, "currentPage": 1})

    @post("/online-logs/force-offline")
    async def force_offline(
        self, data: dict = Body(default={}), _: dict = Depends(require_permission("monitor:manage"))
    ) -> dict:
        """强制下线用户（stub 实现，仅返回成功响应）。"""
        return success_response(message="强制下线成功")

    @get("/get-map-info")
    async def get_map_info(self, _: dict = Depends(require_permission("monitor:view"))) -> dict:
        """获取地图数据（stub 数据）。"""
        map_list = []
        drivers = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]
        for _ in range(50):
            lng = round(random.uniform(113.0, 114.1), 4)
            lat = round(random.uniform(34.0, 35.1), 4)
            plate_number = f"豫A{random.randint(10000, 99999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
            map_list.append(
                {
                    "plateNumber": plate_number,
                    "driver": random.choice(drivers),
                    "orientation": random.randint(1, 360),
                    "lng": lng,
                    "lat": lat,
                }
            )
        return success_response(data=map_list)

    @post("/get-card-list")
    async def get_card_list(
        self, data: dict = Body(default={}), _: dict = Depends(require_permission("monitor:view"))
    ) -> dict:
        """获取卡片列表（stub 数据）。"""
        card_names = ["SSL证书", "人脸识别", "CVM", "云数据库", "T-Sec 云防火墙"]
        banners = [
            "https://tdesign.gtimg.com/tdesign-pro/cloud-server.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/t-sec.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/ssl.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/cloud-db.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/face-recognition.jpg",
        ]
        descriptions = [
            "SSL证书又叫服务器证书，腾讯云为您提供证书的一站式服务，包括免费、付费证书的申请、管理及部署",
            "基于腾讯优图强大的面部分析技术，提供包括人脸检测与分析、五官定位、人脸搜索、人脸比对、人脸验证等功能",
            "云硬盘为您提供用于CVM的持久性数据块级存储服务。云硬盘中的数据自动地在可用区内以多副本冗余",
            "云数据库MySQL为用户提供安全可靠，性能卓越、易于维护的企业级云数据库服务",
            "腾讯安全云防火墙产品，是腾讯云安全团队结合云原生的优势，自主研发的SaaS化防火墙产品",
        ]
        card_list = []
        for i in range(1, 49):
            card_list.append(
                {
                    "index": i,
                    "isSetup": random.choice([True, False]),
                    "type": random.randint(1, 5),
                    "banner": random.choice(banners),
                    "name": random.choice(card_names),
                    "description": random.choice(descriptions),
                }
            )
        return success_response(data={"list": card_list})
