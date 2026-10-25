"""菜单 DTO 的单元测试。

重点覆盖嵌套 `meta` 载荷的扁平化（MenuMetaFlattenMixin）：
接口读写契约都是嵌套 meta（响应为 MenuResponseDTO.meta，前端表单与集成测试
均提交 meta:{title, icon, ...}），但创建/更新 DTO 早期只声明扁平字段，
pydantic 默认忽略额外字段 → 嵌套 meta 被静默丢弃、title 回落为 name。
"""

import pytest
from pydantic import ValidationError

from src.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO


@pytest.mark.unit
class TestMenuDtoMetaFlatten:
    """MenuCreateDTO / MenuUpdateDTO 的嵌套 meta 提升测试。"""

    def test_create_nested_meta_is_flattened(self) -> None:
        """嵌套 meta 的各字段必须提升到顶层扁平字段。"""
        dto = MenuCreateDTO(
            name="user_mgr",
            path="/system/user",
            meta={
                "title": "用户管理",
                "icon": "ri:user-line",
                "rSvgName": "user",
                "isShowMenu": 0,
                "isShowParent": 1,
                "isKeepalive": 1,
                "frameUrl": "",
                "frameLoading": 0,
                "transitionEnter": "animate__fadeIn",
                "transitionLeave": "animate__fadeOut",
                "isHiddenTag": 1,
                "fixedTag": 1,
                "dynamicLevel": 2,
            },
        )
        assert dto.title == "用户管理"
        assert dto.icon == "ri:user-line"
        assert dto.rSvgName == "user"
        assert dto.isShowMenu == 0
        assert dto.isShowParent == 1
        assert dto.isKeepalive == 1
        assert dto.frameLoading == 0
        assert dto.transitionEnter == "animate__fadeIn"
        assert dto.transitionLeave == "animate__fadeOut"
        assert dto.isHiddenTag == 1
        assert dto.fixedTag == 1
        assert dto.dynamicLevel == 2
        # frameUrl 传空串，经 empty_str_to_none 归一为 None
        assert dto.frameUrl is None

    def test_create_flat_fields_still_supported(self) -> None:
        """扁平载荷（向后兼容）不受影响。"""
        dto = MenuCreateDTO(name="flat_menu", title="扁平标题", icon="ri:home-line")
        assert dto.title == "扁平标题"
        assert dto.icon == "ri:home-line"

    def test_nested_meta_wins_over_flat(self) -> None:
        """扁平与嵌套并存时，嵌套值优先。"""
        dto = MenuCreateDTO(name="both", title="扁平标题", meta={"title": "嵌套标题"})
        assert dto.title == "嵌套标题"

    def test_none_value_in_meta_does_not_override_flat(self) -> None:
        """meta 中显式传 None 不覆盖扁平值（与 update_info 的 None 语义一致）。"""
        dto = MenuCreateDTO(name="keep", title="扁平标题", meta={"title": None})
        assert dto.title == "扁平标题"

    def test_meta_none_is_noop(self) -> None:
        """meta 为 None 时原样返回，不抛错。"""
        assert MenuUpdateDTO(rank=1, meta=None).rank == 1

    def test_non_dict_meta_is_rejected(self) -> None:
        """meta 已声明为 dict | None，非法类型直接被 pydantic 拒绝（不再静默忽略）。"""
        with pytest.raises(ValidationError):
            MenuUpdateDTO(rank=2, meta="not-a-dict")  # type: ignore[arg-type]

    def test_update_nested_meta_title(self) -> None:
        """更新载荷中的嵌套 meta.title 必须被提升。"""
        dto = MenuUpdateDTO(rank=99, meta={"title": "已更新菜单"})
        assert dto.title == "已更新菜单"
        assert dto.rank == 99
        # 未提交的字段保持 None（update_info 据此跳过更新）
        assert dto.icon is None

    def test_update_nested_meta_boolean_fields(self) -> None:
        """更新载荷中的布尔型 meta 字段（前端会传 true/false）必须被提升。"""
        dto = MenuUpdateDTO(meta={"isShowMenu": False, "isKeepalive": True})
        assert dto.isShowMenu == 0
        assert dto.isKeepalive == 1

    def test_unknown_meta_keys_are_ignored(self) -> None:
        """meta 中的未知键被忽略，不会因为额外字段报错。"""
        dto = MenuCreateDTO(name="unknown", meta={"title": "标题", "notAField": 1})
        assert dto.title == "标题"
