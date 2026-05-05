"""字典领域实体的单元测试。

测试 DictionaryEntity 的业务规则方法和工厂方法。
"""

import pytest

from src.domain.entities.dictionary import DictionaryEntity


@pytest.mark.unit
class TestDictionaryEntity:
    """DictionaryEntity 测试类。"""

    # ---- 业务规则方法测试 ----

    def test_is_circular_reference_true(self):
        """测试 is_circular_reference 方法（自身引用）。"""
        dictionary = DictionaryEntity(id="dict-1", name="gender", value="1")
        assert dictionary.is_circular_reference("dict-1") is True

    def test_is_circular_reference_different_parent(self):
        """测试 is_circular_reference 方法（不同父节点）。"""
        dictionary = DictionaryEntity(id="dict-1", name="gender", value="1")
        assert dictionary.is_circular_reference("dict-2") is False

    def test_is_circular_reference_none(self):
        """测试 is_circular_reference 方法（无父节点）。"""
        dictionary = DictionaryEntity(id="dict-1", name="gender", value="1")
        assert dictionary.is_circular_reference(None) is False

    # ---- 状态变更方法测试 ----

    def test_update_info_with_all_fields(self):
        """测试 update_info 方法（更新所有字段）。"""
        dictionary = DictionaryEntity(id="dict-1", name="gender", value="1", label="男", sort=1)
        dictionary.update_info(
            name="new-gender",
            label="女",
            value="2",
            sort=2,
            is_active=1,
            parent_id="parent-1",
            description="描述",
        )
        assert dictionary.name == "new-gender"
        assert dictionary.label == "女"
        assert dictionary.value == "2"
        assert dictionary.sort == 2
        assert dictionary.is_active == 1
        assert dictionary.parent_id == "parent-1"
        assert dictionary.description == "描述"

    def test_update_info_with_partial_fields(self):
        """测试 update_info 方法（部分字段）。"""
        dictionary = DictionaryEntity(id="dict-1", name="gender", value="1")
        dictionary.update_info(label="男", sort=1)
        assert dictionary.label == "男"
        assert dictionary.sort == 1
        assert dictionary.value == "1"

    def test_update_info_ignore_none_fields(self):
        """测试 update_info 方法（忽略 None 字段）。"""
        dictionary = DictionaryEntity(id="dict-1", name="gender", value="1", label="原始标签")
        dictionary.update_info(label=None, sort=None)
        assert dictionary.label == "原始标签"
        assert dictionary.sort == 0

    # ---- 工厂方法测试 ----

    def test_create_new(self):
        """测试 create_new 工厂方法。"""
        dictionary = DictionaryEntity.create_new(
            name="gender",
            label="男",
            value="1",
            sort=1,
            parent_id="parent-1",
            description="性别字典",
        )
        assert dictionary.id is not None
        assert len(dictionary.id) == 32
        assert dictionary.name == "gender"
        assert dictionary.label == "男"
        assert dictionary.value == "1"
        assert dictionary.sort == 1
        assert dictionary.parent_id == "parent-1"
        assert dictionary.description == "性别字典"

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        dictionary = DictionaryEntity.create_new(name="status")
        assert dictionary.name == "status"
        assert dictionary.label == ""
        assert dictionary.value == ""
        assert dictionary.sort == 0
        assert dictionary.is_active == 1
        assert dictionary.parent_id is None
