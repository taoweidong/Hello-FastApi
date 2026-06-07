"""IP 规则管理路由模块。

提供 IP 黑白名单规则的增删改查、批量删除、清空等功能。
路由前缀: /api/system/ip-rule
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import list_response, success_response
from src.api.common.response_schemas import ApiResponse, PaginatedResponse
from src.api.dependencies import require_permission
from src.api.dependencies.ip_rule_service import get_ip_rule_service
from src.application.dto.ip_rule_dto import (
    IPRuleBatchDeleteDTO,
    IPRuleCreateDTO,
    IPRuleListQueryDTO,
    IPRuleResponseDTO,
    IPRuleUpdateDTO,
)
from src.application.services.ip_rule_service import IPRuleService
from src.domain.entities.ip_rule import IPRuleEntity


def _to_response(rule: IPRuleEntity) -> dict:
    """将 IPRuleEntity 转为响应字典。"""
    return IPRuleResponseDTO(
        id=rule.id,
        ipAddress=rule.ip_address,
        ruleType=rule.rule_type,
        reason=rule.reason or "",
        isActive=rule.is_active,
        creatorId=rule.creator_id,
        modifierId=rule.modifier_id,
        createdTime=rule.created_time,
        updatedTime=rule.updated_time,
        expiresAt=rule.expires_at,
        description=rule.description or "",
    ).model_dump(mode="json")


class IPRuleRouter(Routable):
    """IP 规则管理路由类，提供 IP 黑白名单规则的增删改查功能。"""

    @post("", response_model=PaginatedResponse[dict])
    async def get_ip_rules(
        self,
        query: IPRuleListQueryDTO,
        service: IPRuleService = Depends(get_ip_rule_service),
        _: dict = Depends(require_permission("ip-rule:view")),
    ) -> dict:
        """获取 IP 规则列表（分页）。"""
        rules, total = await service.get_ip_rules(
            page_num=query.pageNum,
            page_size=query.pageSize,
            rule_type=query.ruleType,
            is_active=query.isActive,
            created_time=query.createdTime,
        )
        rule_list = [_to_response(rule) for rule in rules]
        return list_response(
            list_data=rule_list, total=total, page_size=query.pageSize, current_page=query.pageNum
        )

    @get("/{rule_id}", response_model=ApiResponse[dict])
    async def get_ip_rule(
        self,
        rule_id: str,
        service: IPRuleService = Depends(get_ip_rule_service),
        _: dict = Depends(require_permission("ip-rule:view")),
    ) -> dict:
        """获取 IP 规则详情。"""
        rule = await service.get_ip_rule(rule_id)
        return success_response(data=_to_response(rule))

    @post("/create", response_model=ApiResponse[dict])
    async def create_ip_rule(
        self,
        dto: IPRuleCreateDTO,
        service: IPRuleService = Depends(get_ip_rule_service),
        _: dict = Depends(require_permission("ip-rule:add")),
    ) -> dict:
        """创建 IP 规则。"""
        rule = await service.create_ip_rule(
            ip_address=dto.ipAddress,
            rule_type=dto.ruleType,
            reason=dto.reason,
            is_active=dto.isActive,
            expires_at=dto.expiresAt,
        )
        return success_response(data={"id": rule.id, "ipAddress": rule.ip_address}, message="创建成功", code=201)

    @put("/{rule_id}", response_model=ApiResponse[dict])
    async def update_ip_rule(
        self,
        rule_id: str,
        dto: IPRuleUpdateDTO,
        service: IPRuleService = Depends(get_ip_rule_service),
        _: dict = Depends(require_permission("ip-rule:edit")),
    ) -> dict:
        """更新 IP 规则。"""
        rule = await service.update_ip_rule(
            rule_id=rule_id,
            ip_address=dto.ipAddress,
            rule_type=dto.ruleType,
            reason=dto.reason,
            is_active=dto.isActive,
            expires_at=dto.expiresAt,
            description=dto.description,
        )
        return success_response(data={"id": rule.id, "ipAddress": rule.ip_address}, message="更新成功")

    @delete("/{rule_id}", response_model=ApiResponse[None])
    async def delete_ip_rule(
        self,
        rule_id: str,
        service: IPRuleService = Depends(get_ip_rule_service),
        _: dict = Depends(require_permission("ip-rule:delete")),
    ) -> dict:
        """删除 IP 规则。"""
        await service.delete_ip_rules([rule_id])
        return success_response(message="删除成功")

    @post("/batch-delete", response_model=ApiResponse[dict])
    async def batch_delete_ip_rules(
        self,
        dto: IPRuleBatchDeleteDTO,
        service: IPRuleService = Depends(get_ip_rule_service),
        _: dict = Depends(require_permission("ip-rule:delete")),
    ) -> dict:
        """批量删除 IP 规则。"""
        count = await service.delete_ip_rules(dto.ids)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/clear", response_model=ApiResponse[dict])
    async def clear_ip_rules(
        self,
        service: IPRuleService = Depends(get_ip_rule_service),
        _: dict = Depends(require_permission("ip-rule:delete")),
    ) -> dict:
        """清空所有 IP 规则。"""
        count = await service.clear_ip_rules()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")
