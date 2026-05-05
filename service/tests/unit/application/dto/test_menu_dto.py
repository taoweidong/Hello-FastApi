"""菜单 DTO 的单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.application.dto.menu_dto import MenuCreateDTO, MenuMetaDTO, MenuResponseDTO, MenuUpdateDTO


@pytest.mark.unit
class TestMenuMetaDTO:
    """MenuMetaDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的菜单元数据。"""
        dto = MenuMetaDTO(id="1")
        assert dto.id == "1"
        assert dto.title is None
        assert dto.isShowMenu == 1
        assert dto.isShowParent == 0
        assert dto.isKeepalive == 0
        assert dto.frameLoading == 1
        assert dto.isHiddenTag == 0
        assert dto.fixedTag == 0
        assert dto.dynamicLevel == 0

    def test_with_all_fields(self):
        """测试所有字段。"""
        dto = MenuMetaDTO(id="1", title="用户管理", icon="user", rSvgName="user-svg", isShowMenu=1, isShowParent=1, isKeepalive=1, frameUrl="https://example.com", frameLoading=0, transitionEnter="fade-in", transitionLeave="fade-out", isHiddenTag=1, fixedTag=1, dynamicLevel=2)
        assert dto.title == "用户管理"
        assert dto.icon == "user"
        assert dto.dynamicLevel == 2

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            MenuMetaDTO()


@pytest.mark.unit
class TestMenuCreateDTO:
    """MenuCreateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的菜单创建数据。"""
        dto = MenuCreateDTO(name="用户管理")
        assert dto.name == "用户管理"
        assert dto.parentId is None
        assert dto.menuType == 0
        assert dto.path is None
        assert dto.rank == 0
        assert dto.isActive == 1
        assert dto.isShowMenu == 1
        assert dto.isShowParent == 0
        assert dto.isKeepalive == 0
        assert dto.frameLoading == 1
        assert dto.isHiddenTag == 0
        assert dto.fixedTag == 0
        assert dto.dynamicLevel == 0

    def test_valid_input_all_fields(self):
        """测试所有字段。"""
        dto = MenuCreateDTO(
            name="用户管理",
            parentId="123",
            menuType=1,
            path="/user",
            component="views/user/index.vue",
            rank=1,
            isActive=0,
            method="GET",
            description="用户管理页面",
            title="用户管理",
            icon="user",
            rSvgName="user-svg",
            isShowMenu=1,
            isShowParent=1,
            isKeepalive=1,
            frameUrl="https://example.com",
            frameLoading=0,
            transitionEnter="fade-in",
            transitionLeave="fade-out",
            isHiddenTag=1,
            fixedTag=1,
            dynamicLevel=2,
        )
        assert dto.parentId == "123"
        assert dto.menuType == 1
        assert dto.path == "/user"
        assert dto.dynamicLevel == 2

    def test_empty_parent_id_converts_to_none(self):
        """测试空字符串 parentId 转换为 None。"""
        dto = MenuCreateDTO(name="user", parentId="")
        assert dto.parentId is None

    def test_zero_parent_id_converts_to_none(self):
        """测试 int 0 的 parentId 转换为 None。"""
        dto = MenuCreateDTO(name="user", parentId=0)
        assert dto.parentId is None

    def test_empty_name_raises_error(self):
        """测试空字符串 name 转换为 None 后因必填字段报错。"""
        with pytest.raises(ValidationError):
            MenuCreateDTO(name="")

    def test_empty_path_converts_to_none(self):
        """测试空字符串 path 转换为 None。"""
        dto = MenuCreateDTO(name="user", path="")
        assert dto.path is None

    def test_empty_component_converts_to_none(self):
        """测试空字符串 component 转换为 None。"""
        dto = MenuCreateDTO(name="user", component="")
        assert dto.component is None

    def test_empty_method_converts_to_none(self):
        """测试空字符串 method 转换为 None。"""
        dto = MenuCreateDTO(name="user", method="")
        assert dto.method is None

    def test_empty_icon_converts_to_none(self):
        """测试空字符串 icon 转换为 None。"""
        dto = MenuCreateDTO(name="user", icon="")
        assert dto.icon is None

    def test_empty_frame_url_converts_to_none(self):
        """测试空字符串 frameUrl 转换为 None。"""
        dto = MenuCreateDTO(name="user", frameUrl="")
        assert dto.frameUrl is None

    def test_name_too_long(self):
        """测试菜单名称超长。"""
        with pytest.raises(ValidationError):
            MenuCreateDTO(name="a" * 129)

    def test_missing_name(self):
        """测试缺少菜单名称。"""
        with pytest.raises(ValidationError):
            MenuCreateDTO()


@pytest.mark.unit
class TestMenuUpdateDTO:
    """MenuUpdateDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的菜单更新数据。"""
        dto = MenuUpdateDTO(name="新菜单")
        assert dto.name == "新菜单"

    def test_empty_input(self):
        """测试空更新。"""
        dto = MenuUpdateDTO()
        assert dto.name is None
        assert dto.menuType is None
        assert dto.isActive is None

    def test_empty_name_converts_to_none(self):
        """测试空字符串 name 转换为 None。"""
        dto = MenuUpdateDTO(name="")
        assert dto.name is None

    def test_empty_path_converts_to_none(self):
        """测试空字符串 path 转换为 None。"""
        dto = MenuUpdateDTO(path="")
        assert dto.path is None

    def test_empty_parent_id_converts_to_none(self):
        """测试空字符串 parentId 转换为 None。"""
        dto = MenuUpdateDTO(parentId="")
        assert dto.parentId is None

    def test_zero_parent_id_converts_to_none(self):
        """测试 int 0 的 parentId 转换为 None。"""
        dto = MenuUpdateDTO(parentId=0)
        assert dto.parentId is None


@pytest.mark.unit
class TestMenuResponseDTO:
    """MenuResponseDTO 验证测试。"""

    def test_valid_input(self):
        """测试有效的菜单响应数据。"""
        dto = MenuResponseDTO(id="1", name="用户管理", metaId="m1")
        assert dto.id == "1"
        assert dto.name == "用户管理"
        assert dto.metaId == "m1"
        assert dto.menuType == 0
        assert dto.isActive == 1
        assert dto.children == []
        assert dto.meta is None

    def test_with_all_fields(self):
        """测试所有字段。"""
        now = datetime.now()
        meta = MenuMetaDTO(id="m1", title="用户管理")
        dto = MenuResponseDTO(
            id="1",
            parentId="0",
            menuType=1,
            name="用户管理",
            path="/user",
            component="views/user/index.vue",
            rank=1,
            isActive=1,
            method="GET",
            metaId="m1",
            meta=meta,
            creatorId="u1",
            modifierId="u2",
            createdTime=now,
            updatedTime=now,
            description="描述",
            children=[MenuResponseDTO(id="2", name="子菜单", metaId="m2")],
        )
        assert dto.menuType == 1
        assert dto.meta is not None
        assert dto.meta.title == "用户管理"
        assert len(dto.children) == 1
        assert dto.children[0].name == "子菜单"

    def test_missing_id(self):
        """测试缺少 ID。"""
        with pytest.raises(ValidationError):
            MenuResponseDTO(name="用户管理", metaId="m1")

    def test_missing_meta_id_defaults_to_empty(self):
        """测试缺少 metaId 时默认为空字符串。"""
        dto = MenuResponseDTO(id="1", name="用户管理")
        assert dto.metaId == ""
