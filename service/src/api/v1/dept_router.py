"""部门管理路由模块。

提供部门的增删改查功能。
新字段: modeType(权限模式), code(编码), rank(排序号), autoBind(自动绑定角色), isActive(是否启用), description(描述)
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

from classy_fastapi import Routable, delete, post, put
from fastapi import Body, Depends

from src.api.common import success_response
from src.api.dependencies import get_department_service, require_permission
from src.application.dto.department_dto import DepartmentCreateDTO, DepartmentListQueryDTO, DepartmentUpdateDTO
from src.application.services.department_service import DepartmentService


class DeptRouter(Routable):
    """部门管理路由类，提供部门增删改查功能。"""

    @post("/dept")
    async def get_dept_list(self, data: dict = Body(default={}), service: DepartmentService = Depends(get_department_service), _: dict = Depends(require_permission("dept:view"))) -> dict:
        """获取部门列表（扁平结构）。"""
        query = DepartmentListQueryDTO(name=data.get("name"), isActive=data.get("isActive"))
        departments = await service.get_departments(query)
        dept_list = [dept.model_dump() for dept in departments]
        return success_response(data=dept_list)

    @post("/dept/create")
    async def create_department(self, dto: DepartmentCreateDTO, service: DepartmentService = Depends(get_department_service), _: dict = Depends(require_permission("dept:add"))) -> dict:
        """创建部门。"""
        department = await service.create_department(dto)
        return success_response(data={"id": department.id, "name": department.name}, message="创建成功", code=201)

    @put("/dept/{dept_id}")
    async def update_department(self, dept_id: str, dto: DepartmentUpdateDTO, service: DepartmentService = Depends(get_department_service), _: dict = Depends(require_permission("dept:edit"))) -> dict:
        """更新部门。"""
        department = await service.update_department(dept_id, dto)
        return success_response(data={"id": department.id, "name": department.name}, message="更新成功")

    @delete("/dept/{dept_id}")
    async def delete_department(self, dept_id: str, service: DepartmentService = Depends(get_department_service), _: dict = Depends(require_permission("dept:delete"))) -> dict:
        """删除部门。"""
        await service.delete_department(dept_id)
        return success_response(message="删除成功")
