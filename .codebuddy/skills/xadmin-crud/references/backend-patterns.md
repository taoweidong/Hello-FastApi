# 后端代码模式 - xadmin

> 本文件包含后端各层代码的完整模板。适配新项目时，修改代码模板中的基类名和导入路径即可。

## Model 模式

### 基本模板

```python
from django.db import models
from django.utils import timezone

from common.core.models import DbAuditModel, upload_directory_path, AutoCleanFileMixin
from common.fields.image import ProcessedImageField
from system.models import UserInfo, UploadFile


class {ModelName}(AutoCleanFileMixin, DbAuditModel):
    """
    注意：AutoCleanFileMixin 仅在有文件/图片字段时混入，否则只继承 DbAuditModel
    注意：跳过基类已有字段：id, created_time, updated_time, description, creator, modifier, dept_belong
    """

    # choices 枚举
    class {EnumName}Choices(models.IntegerChoices):
        VALUE1 = 0, "选项1"
        VALUE2 = 1, "选项2"

    # choices 单选字段
    {field_name} = models.SmallIntegerField(choices={EnumName}Choices, default={EnumName}Choices.VALUE1,
                                            verbose_name="{字段注释}")

    # ForeignKey 一对多
    {fk_field} = models.ForeignKey(to={RelatedModel}, verbose_name="{字段注释}",
                                    on_delete=models.CASCADE, related_name="{table}_{fk_field}")

    # ManyToManyField 多对多
    {m2m_field} = models.ManyToManyField(to={RelatedModel}, verbose_name="{字段注释}",
                                          blank=True, related_name="{table}_{m2m_field}")

    # 图片上传（原图）
    {image_field} = models.ImageField(verbose_name="{字段注释}", null=True, blank=True)

    # 文件上传
    {file_field} = models.FileField(verbose_name="{字段注释}", upload_to=upload_directory_path,
                                     null=True, blank=True)

    # 单文件关联
    {single_file} = models.ForeignKey(to=UploadFile, related_name="{table}_{single_file}",
                                       verbose_name="{字段注释}", blank=True, on_delete=models.CASCADE)

    # 多文件关联
    {multi_file} = models.ManyToManyField(to=UploadFile, related_name="{table}_{multi_file}",
                                           verbose_name="{字段注释}", blank=True)

    # 普通字段
    {char_field} = models.CharField(verbose_name="{字段注释}", max_length={n})
    {text_field} = models.TextField(verbose_name="{字段注释}", null=True, blank=True)
    {int_field} = models.IntegerField(verbose_name="{字段注释}", default=0)
    {float_field} = models.FloatField(verbose_name="{字段注释}", default=0.0)
    {decimal_field} = models.DecimalField(verbose_name="{字段注释}", max_digits={p}, decimal_places={s}, default=0)
    {bool_field} = models.BooleanField(verbose_name="{字段注释}", default=False)
    {datetime_field} = models.DateTimeField(verbose_name="{字段注释}", default=timezone.now)
    {date_field} = models.DateField(verbose_name="{字段注释}", null=True, blank=True)
    {json_field} = models.JSONField(verbose_name="{字段注释}", null=True, blank=True)

    class Meta:
        verbose_name = '{模型中文名}'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.{主要展示字段}}"
```

### 实际示例 - Book

```python
from django.db import models
from django.utils import timezone
from pilkit.processors import ResizeToFill

from common.core.models import DbAuditModel, upload_directory_path, AutoCleanFileMixin
from common.fields.image import ProcessedImageField
from system.models import UserInfo, UploadFile


class Book(AutoCleanFileMixin, DbAuditModel):
    class CategoryChoices(models.IntegerChoices):
        DIRECTORY = 0, "小说"
        MENU = 1, "文学"
        PERMISSION = 2, "哲学"

    category = models.SmallIntegerField(choices=CategoryChoices, default=CategoryChoices.DIRECTORY,
                                        verbose_name="书籍类型")
    admin = models.ForeignKey(to=UserInfo, verbose_name="管理员1", on_delete=models.CASCADE)
    admin2 = models.ForeignKey(to=UserInfo, verbose_name="管理员2", on_delete=models.CASCADE,
                               related_name="book_admin2")
    managers = models.ManyToManyField(to=UserInfo, verbose_name="操作人员1", blank=True, related_name="book_managers")

    name = models.CharField(verbose_name="书籍名称", max_length=100)
    isbn = models.CharField(verbose_name="标准书号", max_length=20)
    author = models.CharField(verbose_name="书籍作者", max_length=20)
    publisher = models.CharField(verbose_name="出版社", max_length=20, default='大宇出版社')
    publication_date = models.DateTimeField(verbose_name="出版日期", default=timezone.now)
    price = models.FloatField(verbose_name="书籍售价", default=999.99)
    is_active = models.BooleanField(verbose_name="是否启用", default=False)

    class Meta:
        verbose_name = '书籍名称'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name}"
```

## Serializer 模式

### 基本模板

```python
from rest_framework import serializers

from common.core.serializers import BaseModelSerializer, TabsColumn
from common.fields.utils import input_wrapper
from {app} import models


class {ModelName}Serializer(BaseModelSerializer):
    class Meta:
        model = models.{ModelName}

        # 方式1：使用 tabs 表单分组（推荐字段多时使用）
        tabs = [
            TabsColumn('基本信息', ['{field1}', '{field2}', ...]),
            TabsColumn('关联信息', ['{fk_field1}', '{fk_field2}', ...]),
        ]
        fields = ['pk']  # tabs 模式下 fields 只需 ['pk']，tabs 中的字段会自动合并

        # 方式2：普通单表单（字段少时使用）
        # fields = ['pk', '{field1}', '{field2}', ..., 'created_time', 'updated_time']

        # 表格展示字段（控制前端 table 显示哪些列及顺序）
        table_fields = ['pk', '{展示字段1}', '{展示字段2}', ...]

        # 字段额外参数
        extra_kwargs = {
            'pk': {'read_only': True},
            # ForeignKey 字段
            '{fk_field}': {
                'attrs': ['pk', '{关联模型可读字段}'],
                'required': True,
                'format': "{{可读字段名}}({{pk}})",
            },
            # ManyToManyField 字段
            '{m2m_field}': {
                'attrs': ['pk', '{关联模型可读字段}'],
                'required': False,
                'format': "{{可读字段名}}({{pk}})",
            },
            # UploadFile 关联（单文件）
            '{single_file}': {
                'attrs': ['pk', 'filepath', 'filesize', 'filename'],
                'required': True,
                'format': "{filename}({pk})",
                'ignore_field_permission': True,
            },
            # UploadFile 关联（多文件）
            '{multi_file}': {
                'attrs': ['pk', 'filepath', 'filesize', 'filename'],
                'required': False,
                'format': "{filename}({pk})",
                'ignore_field_permission': True,
            },
        }
```

### 实际示例 - BookSerializer

```python
from rest_framework import serializers

from common.core.serializers import BaseModelSerializer, TabsColumn
from common.fields.utils import input_wrapper
from demo import models


class BookSerializer(BaseModelSerializer):
    class Meta:
        model = models.Book

        tabs = [
            TabsColumn('基本信息',
                       ['name', 'isbn', 'category', 'is_active', 'author', 'publisher', 'publication_date', 'price',
                        'created_time', 'updated_time']),
            TabsColumn('管理员', ['admin', 'admin2', 'managers', 'managers2']),
            TabsColumn('文件信息', ['avatar', 'cover', 'book_file', 'file', 'files'])
        ]
        fields = ['pk', 'block']

        table_fields = [
            'pk', 'cover', 'category', 'name', 'is_active', 'isbn', 'author', 'publisher', 'publication_date', 'price',
            'book_file', 'file', 'files'
        ]

        extra_kwargs = {
            'pk': {'read_only': True},
            'admin': {
                'attrs': ['pk', 'username'], 'required': True, 'format': "{username}({pk})",
                'input_type': 'api-search-user'
            },
            'admin2': {
                'attrs': ['pk', 'username'], 'required': True, 'format': "{username}({pk})",
            },
            'managers': {
                'attrs': ['pk', 'username'], 'required': True, 'format': "{username}({pk})",
                'input_type': 'api-search-user'
            },
            'files': {
                'attrs': ['pk', 'filepath', 'filesize', 'filename'], 'required': False, 'format': "{filename}({pk})",
                'ignore_field_permission': True
            },
            'file': {
                'attrs': ['pk', 'filepath', 'filesize', 'filename'], 'required': True, 'format': "{filename}({pk})",
                'ignore_field_permission': True, 'input_type_suffix': 'image'
            }
        }
```

## ViewSet + FilterSet 模式

### 基本模板

```python
from django_filters import rest_framework as filters

from common.core.filter import BaseFilterSet, PkMultipleFilter
from common.core.modelset import BaseModelSet, ImportExportDataAction
from common.core.pagination import DynamicPageNumber
from common.utils import get_logger
from {app}.models import {ModelName}
from {app}.serializers.{table_name} import {ModelName}Serializer

logger = get_logger(__name__)


class {ModelName}Filter(BaseFilterSet):
    # 字符串字段用 icontains 模糊搜索
    {char_field} = filters.CharFilter(field_name='{char_field}', lookup_expr='icontains')

    # ForeignKey/ManyToManyField 用 PkMultipleFilter
    {fk_field} = PkMultipleFilter(input_type='input')

    class Meta:
        model = {ModelName}
        fields = [{搜索字段列表}]  # fields 用于前端自动生成搜索表单


class {ModelName}ViewSet(BaseModelSet, ImportExportDataAction):
    """{模型中文名}"""  # docstring 必须写，用于菜单和日志显示
    queryset = {ModelName}.objects.all()
    serializer_class = {ModelName}Serializer
    ordering_fields = ['created_time']
    filterset_class = {ModelName}Filter
```

### 实际示例 - BookViewSet

```python
from django_filters import rest_framework as filters
from rest_framework.decorators import action

from common.core.filter import BaseFilterSet, PkMultipleFilter
from common.core.modelset import BaseModelSet, ImportExportDataAction
from common.core.pagination import DynamicPageNumber
from common.core.response import ApiResponse
from common.utils import get_logger
from demo.models import Book
from demo.serializers.book import BookSerializer

logger = get_logger(__name__)


class BookViewSetFilter(BaseFilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    author = filters.CharFilter(field_name='author', lookup_expr='icontains')
    publisher = filters.CharFilter(field_name='publisher', lookup_expr='icontains')
    managers2 = PkMultipleFilter(input_type='api-search-user')
    managers = PkMultipleFilter(input_type='input')

    class Meta:
        model = Book
        fields = ['name', 'isbn', 'author', 'publisher', 'is_active', 'publication_date', 'price',
                  'created_time', 'managers', 'managers2']


class BookViewSet(BaseModelSet, ImportExportDataAction):
    """书籍"""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    ordering_fields = ['created_time']
    filterset_class = BookViewSetFilter
    pagination_class = DynamicPageNumber(1000)
```

## URL 模式

### 基本模板

```python
from rest_framework.routers import SimpleRouter

from {app}.views.{table_name} import {ModelName}ViewSet

app_name = '{app}'

router = SimpleRouter(False)  # False 去掉 URL 尾部斜线

router.register('{route_prefix}', {ModelName}ViewSet, basename='{route_prefix}')

urlpatterns = []
urlpatterns += router.urls
```

### 实际示例 - demo/urls.py

```python
from rest_framework.routers import SimpleRouter

from demo.views import BookViewSet

app_name = 'demo'

router = SimpleRouter(False)

router.register('book', BookViewSet, basename='book')

urlpatterns = []
urlpatterns += router.urls
```

## App 配置模式

### apps.py

```python
from django.apps import AppConfig


class {AppName}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app}'
```

### config.py

```python
from django.urls import path, include

# 路由配置，当添加APP完成时候，会自动注入路由到总服务
URLPATTERNS = [
    path('api/{app}/', include('{app}.urls')),
]
# 请求白名单，支持正则表达式
PERMISSION_WHITE_REURL = []
```

### __init__.py

空文件

### models/__init__.py

```python
from .{table_name} import *
```

### serializers/__init__.py

```python
from .{table_name} import *
```

## 文件追加策略

### 追加 Model 到已有 app

1. 创建 `{app}/models/{table_name}.py`
2. 在 `{app}/models/__init__.py` 末尾追加：`from .{table_name} import *`

### 追加 Serializer 到已有 app

1. 创建 `{app}/serializers/{table_name}.py`
2. 在 `{app}/serializers/__init__.py` 末尾追加：`from .{table_name} import *`

### 追加 ViewSet 到已有 app

1. 创建 `{app}/views/{table_name}.py`（或追加到 `{app}/views.py`）
2. 在 `{app}/urls.py` 中：
   - 追加 import：`from {app}.views.{table_name} import {ModelName}ViewSet`
   - 追加注册：`router.register('{route_prefix}', {ModelName}ViewSet, basename='{route_prefix}')`
