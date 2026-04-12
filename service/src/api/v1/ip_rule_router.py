"""IP 规则管理路由模块。

提供 IP 黑白名单规则的增删改查、批量删除、清空等功能。
路由前缀: /api/system/ip-rule
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Body, Depends

from src.api.common import list_response, success_response
from src.api.dependencies import require_permission
from src.api.dependencies.ip_rule_service import get_ip_rule_service
from src.application.services.ip_rule_service import IPRuleService


class IPRuleRouter(Routable):
    """IP 规则管理路由类，提供 IP 黑白名单规则的增删改查功能。"""

    @post("")
    async def get_ip_rules(self, data: dict = Body(default={}), service: IPRuleService = Depends(get_ip_rule_service), _: dict = Depends(require_permission("ip-rule:view"))) -> dict:
        """获取 IP 规则列表（分页）。"""
        page_num = data.get("pageNum", 1)
        page_size = data.get("pageSize", 10)
        rule_type = data.get("ruleType")
        is_active = data.get("isActive")
        created_time = data.get("createdTime")

        if is_active is not None:
            is_active = int(is_active)

        rules, total = await service.get_ip_rules(
            page_num=page_num,
            page_size=page_size,
            rule_type=rule_type,
            is_active=is_active,
            created_time=created_time,
        )
        rule_list = []
        for rule in rules:
            rule_list.append({
                "id": rule.id,
                "ipAddress": rule.ip_address,
                "ruleType": rule.rule_type,
                "reason": rule.reason or "",
                "isActive": rule.is_active,
                "creatorId": rule.creator_id,
                "modifierId": rule.modifier_id,
                "createdTime": rule.created_time.isoformat() if rule.created_time else None,
                "updatedTime": rule.updated_time.isoformat() if rule.updated_time else None,
                "expiresAt": rule.expires_at.isoformat() if rule.expires_at else None,
                "description": rule.description or "",
            })
        return list_response(list_data=rule_list, total=total, page_size=page_size, current_page=page_num)

    @get("/{rule_id}")
    async def get_ip_rule(self, rule_id: str, service: IPRuleService = Depends(get_ip_rule_service), _: dict = Depends(require_permission("ip-rule:view"))) -> dict:
        """获取 IP 规则详情。"""
        rule = await service.get_ip_rule(rule_id)
        return success_response(data={
            "id": rule.id,
            "ipAddress": rule.ip_address,
            "ruleType": rule.rule_type,
            "reason": rule.reason or "",
            "isActive": rule.is_active,
            "creatorId": rule.creator_id,
            "modifierId": rule.modifier_id,
            "createdTime": rule.created_time.isoformat() if rule.created_time else None,
            "updatedTime": rule.updated_time.isoformat() if rule.updated_time else None,
            "expiresAt": rule.expires_at.isoformat() if rule.expires_at else None,
            "description": rule.description or "",
        })

    @post("/create")
    async def create_ip_rule(self, data: dict = Body(default={}), service: IPRuleService = Depends(get_ip_rule_service), _: dict = Depends(require_permission("ip-rule:add"))) -> dict:
        """创建 IP 规则。"""
        from datetime import datetime

        expires_at = None
        if data.get("expiresAt"):
            try:
                expires_at = datetime.fromisoformat(data["expiresAt"])
            except ValueError:
                expires_at = None

        rule = await service.create_ip_rule(
            ip_address=data.get("ipAddress", ""),
            rule_type=data.get("ruleType", "blacklist"),
            reason=data.get("reason"),
            is_active=int(data.get("isActive", 1)),
            expires_at=expires_at,
        )
        return success_response(data={"id": rule.id, "ipAddress": rule.ip_address}, message="创建成功", code=201)

    @put("/{rule_id}")
    async def update_ip_rule(self, rule_id: str, data: dict = Body(default={}), service: IPRuleService = Depends(get_ip_rule_service), _: dict = Depends(require_permission("ip-rule:edit"))) -> dict:
        """更新 IP 规则。"""
        from datetime import datetime

        expires_at = None
        if data.get("expiresAt"):
            try:
                expires_at = datetime.fromisoformat(data["expiresAt"])
            except ValueError:
                expires_at = None

        rule = await service.update_ip_rule(
            rule_id=rule_id,
            ip_address=data.get("ipAddress"),
            rule_type=data.get("ruleType"),
            reason=data.get("reason"),
            is_active=int(data["isActive"]) if data.get("isActive") is not None else None,
            expires_at=expires_at,
            description=data.get("description"),
        )
        return success_response(data={"id": rule.id, "ipAddress": rule.ip_address}, message="更新成功")

    @delete("/{rule_id}")
    async def delete_ip_rule(self, rule_id: str, service: IPRuleService = Depends(get_ip_rule_service), _: dict = Depends(require_permission("ip-rule:delete"))) -> dict:
        """删除 IP 规则。"""
        await service.delete_ip_rules([rule_id])
        return success_response(message="删除成功")

    @post("/batch-delete")
    async def batch_delete_ip_rules(self, data: dict = Body(default={}), service: IPRuleService = Depends(get_ip_rule_service), _: dict = Depends(require_permission("ip-rule:delete"))) -> dict:
        """批量删除 IP 规则。"""
        ids = data.get("ids", [])
        count = await service.delete_ip_rules(ids)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/clear")
    async def clear_ip_rules(self, service: IPRuleService = Depends(get_ip_rule_service), _: dict = Depends(require_permission("ip-rule:delete"))) -> dict:
        """清空所有 IP 规则。"""
        count = await service.clear_ip_rules()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")
