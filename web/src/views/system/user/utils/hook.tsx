import "./reset.css";
import dayjs from "dayjs";
import roleForm from "../form/role.vue";
import editForm from "../form/index.vue";
import { ZxcvbnFactory } from "@zxcvbn-ts/core";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import userAvatar from "@/assets/user.jpg";
import { usePublicHooks, formatHigherDeptOptions } from "../../hooks";
import { GenderChoices } from "../../constants";
import { addDialog } from "@/components/ReDialog";
import { useDict, dictLabel } from "@/composables/useDict";
import {
  isNetworkLevelError,
  isRequestCanceled
} from "@/composables/useCrudTable";
import type { PaginationProps } from "@pureadmin/table";
import ReCropperPreview from "@/components/ReCropperPreview";
import type { FormItemProps, RoleFormItemProps } from "../utils/types";
import {
  getKeyList,
  isAllEmpty,
  hideTextAtIndex,
  deviceDetection
} from "@pureadmin/utils";
import { useDebounceFn } from "@vueuse/core";
import { userApi } from "@/api/system/user";
import { deptApi } from "@/api/system/dept";
import { postApi, type PostOption } from "@/api/system/post";
import {
  ElForm,
  ElInput,
  ElFormItem,
  ElProgress,
  ElMessageBox
} from "element-plus";
import {
  type Ref,
  h,
  ref,
  toRaw,
  watch,
  computed,
  reactive,
  onMounted,
  onScopeDispose
} from "vue";

export function useUser(tableRef: Ref) {
  const form = reactive({
    deptId: "",
    username: "",
    phone: "",
    isActive: ""
  });
  const formRef = ref();
  const ruleFormRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const avatarInfo = ref();
  const switchLoadMap = ref({});
  const { switchStyle } = usePublicHooks();
  const higherDeptOptions = ref();
  const selectedNum = ref(0);
  /** 性别字典（后端字典取数，未命中时回退本地 GenderChoices） */
  const dicts = useDict("sys_user_sex");
  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });
  const columns: TableColumnList = [
    {
      label: "勾选列",
      type: "selection",
      fixed: "left",
      reserveSelection: true
    },
    {
      label: "用户编号",
      prop: "id",
      width: 90
    },
    {
      label: "用户头像",
      prop: "avatar",
      cellRenderer: ({ row }) => (
        <el-image
          fit="cover"
          preview-teleported={true}
          src={row.avatar || userAvatar}
          preview-src-list={Array.of(row.avatar || userAvatar)}
          class="size-6 rounded-full align-middle"
        />
      ),
      width: 90
    },
    {
      label: "用户名称",
      prop: "username",
      minWidth: 130
    },
    {
      label: "用户昵称",
      prop: "nickname",
      minWidth: 130
    },
    {
      label: "性别",
      prop: "gender",
      minWidth: 90,
      cellRenderer: ({ row, props }) => {
        const options = dicts["sys_user_sex"].length
          ? dicts["sys_user_sex"]
          : GenderChoices.map(c => ({
              label: c.label,
              value: String(c.value)
            }));
        return (
          <el-tag
            size={props.size}
            type={row.gender === 1 ? "danger" : null}
            effect="plain"
          >
            {dictLabel(options, row.gender, "未知")}
          </el-tag>
        );
      }
    },
    {
      label: "部门",
      prop: "dept.name",
      minWidth: 90
    },
    {
      label: "手机号码",
      prop: "phone",
      minWidth: 90,
      formatter: ({ phone }) =>
        phone ? hideTextAtIndex(phone, { start: 3, end: 6 }) : "-"
    },
    {
      label: "邮箱",
      prop: "email",
      minWidth: 160,
      showOverflowTooltip: true
    },
    {
      label: "状态",
      prop: "isActive",
      minWidth: 90,
      cellRenderer: scope => (
        <el-switch
          size={scope.props.size === "small" ? "small" : "default"}
          loading={switchLoadMap.value[scope.row.id]?.loading}
          model-value={scope.row.isActive}
          active-value={1}
          inactive-value={0}
          active-text="已启用"
          inactive-text="已停用"
          inline-prompt
          style={switchStyle.value}
          onChange={() => onChange(scope as any)}
        />
      )
    },
    {
      label: "创建时间",
      minWidth: 160,
      prop: "createdTime",
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "描述",
      prop: "description",
      minWidth: 160,
      showOverflowTooltip: true
    },
    {
      label: "更新时间",
      prop: "updatedTime",
      minWidth: 160,
      formatter: ({ updatedTime }) =>
        updatedTime ? dayjs(updatedTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "操作",
      fixed: "right",
      width: 180,
      slot: "operation"
    }
  ];
  const buttonClass = computed(() => {
    return [
      "h-5!",
      "reset-margin",
      /*
       * 原为 text-gray-500! + dark:text-white! + dark:hover:text-primary!：
       * 两套固定灰阶靠 dark 变体硬切，与主题色体系脱节。
       * 改用 Element 文本色变量后浅/深色自动适配。
       */
      "text-[var(--el-text-color-secondary)]!",
      "hover:text-primary!"
    ];
  });
  const pwdForm = reactive({
    newPwd: ""
  });
  const pwdProgress = [
    { color: "#e74242", text: "非常弱" },
    { color: "#EFBD47", text: "弱" },
    { color: "#ffa500", text: "一般" },
    { color: "#1bbf1b", text: "强" },
    { color: "#008000", text: "非常强" }
  ];
  const curScore = ref();
  const roleOptions = ref([]);
  const zxcvbnFactory = new ZxcvbnFactory();
  /** 启用岗位下拉选项（用户表单岗位多选） */
  const postOptions = ref<PostOption[]>([]);

  /** 状态变更确认 + API 调用（受控模式：点击时行数据尚未翻转，目标状态取反） */
  function onChange({ row }) {
    const target = row.isActive === 1 ? 0 : 1;
    ElMessageBox.confirm(
      `确认要<strong>${
        target === 1 ? "启用" : "停用"
      }</strong><strong style='color:var(--el-color-primary)'>${
        row.username
      }</strong>用户吗?`,
      "系统提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
        dangerouslyUseHTMLString: true,
        draggable: true
      }
    )
      .then(async () => {
        switchLoadMap.value[row.id] = Object.assign(
          {},
          switchLoadMap.value[row.id],
          {
            loading: true
          }
        );
        try {
          const { code } = await userApi.updateStatus(row.id, {
            isActive: target
          });
          if (code === 0) {
            // 确认且后端成功后才受控翻转开关
            row.isActive = target;
            message("已成功修改用户状态", { type: "success" });
          } else {
            message("修改用户状态失败", { type: "error" });
          }
        } catch {
          message("修改用户状态失败", { type: "error" });
        } finally {
          switchLoadMap.value[row.id] = Object.assign(
            {},
            switchLoadMap.value[row.id],
            {
              loading: false
            }
          );
        }
      })
      .catch(() => {
        // 用户取消确认：开关保持原状态（受控模式下无需回滚）
      });
  }

  /** 下拉菜单「上传头像」按钮的占位回调（实际入口为 handleUpload） */
  function handleUpdate(_row) {}

  /** 删除用户（确认已由页面 popconfirm 完成，这里直接执行删除） */
  async function handleDelete(row) {
    try {
      const { code } = await userApi.destroy(row.id);
      if (code === 0) {
        message(`已成功删除用户 ${row.username}`, { type: "success" });
        // 当前页仅剩这一条且不在首页时页码回退，避免刷新后落在空页
        if (dataList.value.length === 1 && pagination.currentPage > 1) {
          pagination.currentPage -= 1;
        }
        onSearch();
      }
    } catch {
      // 删除请求失败：给出明确提示，用户可重试而不是无感知失败
      message("删除用户失败，请稍后重试", { type: "error" });
    }
  }

  /** 每页条数变化：改 pageSize 后旧页码可能超出新的总页数，先回到第 1 页再刷新 */
  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    pagination.currentPage = 1;
    onSearch();
  }

  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  function handleSelectionChange(val) {
    const prevNum = selectedNum.value;
    selectedNum.value = val.length;
    // 仅在选择条出现/消失（勾选数跨越 0）时重算表格自适应高度，普通勾选不强制重排
    if ((prevNum === 0) !== (selectedNum.value === 0)) {
      tableRef.value.setAdaptive();
    }
  }

  function onSelectionCancel() {
    selectedNum.value = 0;
    tableRef.value.getTableRef().clearSelection();
  }

  /** 批量删除用户（确认已由页面 popconfirm 完成，这里直接执行删除） */
  async function onbatchDel() {
    const curSelected = tableRef.value.getTableRef().getSelectionRows();
    const userIds = getKeyList(curSelected, "id");
    if (!userIds.length) return;
    try {
      const { code } = await userApi.batchDelete(userIds);
      if (code === 0) {
        message(`已成功删除 ${userIds.length} 个用户`, { type: "success" });
        tableRef.value.getTableRef().clearSelection();
        // 当前页数据全部删完且不在首页时页码回退，避免刷新后落在空页
        if (
          dataList.value.length <= userIds.length &&
          pagination.currentPage > 1
        ) {
          pagination.currentPage -= 1;
        }
        onSearch();
      }
    } catch {
      // 删除请求失败：给出明确提示
      message("批量删除用户失败，请稍后重试", { type: "error" });
    }
  }

  /** 当前搜索请求的取消控制器：新搜索发起前 abort 上一次，防止慢响应覆盖新结果 */
  let searchController: AbortController | null = null;

  async function onSearch() {
    // 竞态防护：取消上一次未完成的搜索请求
    searchController?.abort();
    const controller = new AbortController();
    searchController = controller;
    loading.value = true;
    try {
      const { code, data } = await userApi.list(
        {
          ...toRaw(form),
          pageNum: pagination.currentPage,
          pageSize: pagination.pageSize
        },
        { signal: controller.signal }
      );
      // 已被更新的搜索取代：丢弃过期结果，数据与 loading 交给最新请求
      if (controller.signal.aborted) return;
      if (code === 0) {
        dataList.value = data.list;
        pagination.total = data.total;
        pagination.pageSize = data.pageSize;
        pagination.currentPage = data.currentPage;
      }
    } catch (error) {
      /*
       * 请求被取消属于竞态防护的正常路径：静默返回，不提示、不覆盖数据，
       * loading 由最新请求接管；断网/5xx 已由全局响应拦截器统一提示，
       * 这里静默复位 loading 即可，仅 4xx 等业务错误做本地提示，避免重复 toast。
       */
      if (isRequestCanceled(error)) return;
      if (!isNetworkLevelError(error)) {
        message("用户列表加载失败，请稍后重试", { type: "error" });
      }
    } finally {
      // 仅当本次请求仍是最新搜索时才复位 loading，避免取消旧请求时误关新请求的加载态
      if (searchController === controller) {
        loading.value = false;
      }
    }
  }

  const resetForm = formEl => {
    if (!formEl) return;
    formEl.resetFields();
    form.deptId = "";
    onSearch();
  };

  async function openDialog(title = "新增", row?: FormItemProps) {
    /** 表单区加载态：编辑时异步回填已分配岗位期间遮罩表单 */
    const formLoading = ref(false);
    /**
     * reactive 传入 ReDialog：先同步开窗，岗位异步回填后经同一响应式
     * 对象直接更新表单，无需等待请求完成
     */
    const formInline = reactive<FormItemProps>({
      title,
      higherDeptOptions: formatHigherDeptOptions(higherDeptOptions.value),
      parentId: row?.dept?.id ?? 0,
      nickname: row?.nickname ?? "",
      username: row?.username ?? "",
      password: row?.password ?? "",
      phone: row?.phone ?? "",
      email: row?.email ?? "",
      gender: row?.gender ?? "",
      isActive: row?.isActive ?? 1,
      postOptions: postOptions.value ?? [],
      postIds: [],
      description: row?.description ?? ""
    });
    addDialog({
      title: `${title}用户`,
      props: {
        formInline
      },
      // 弹窗宽度分档：多列表单 720px（全局 max-width: 92vw 兜底窄屏）
      width: "720px",
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      sureBtnLoading: true,
      contentRenderer: () =>
        h(editForm, {
          ref: formRef,
          formInline: null,
          formLoading: formLoading.value
        }),
      beforeSure: (done, { options, closeLoading }) => {
        const FormRef = formRef.value.getRef();
        const curData = options.props.formInline as FormItemProps;

        FormRef.validate(async valid => {
          if (valid) {
            try {
              const payload = {
                username: curData.username,
                password: curData.password,
                nickname: curData.nickname || null,
                email: curData.email || null,
                phone: curData.phone || null,
                gender: curData.gender || null,
                isActive: curData.isActive,
                deptId: curData.parentId || null,
                postIds: curData.postIds ?? [],
                description: curData.description || null
              };

              if (title === "新增") {
                const { code } = await userApi.create(payload);
                if (code === 0 || code === 201) {
                  message(`成功创建用户 ${curData.username}`, {
                    type: "success"
                  });
                  done();
                  onSearch();
                  return;
                }
              } else {
                const { code } = await userApi.partialUpdate(
                  String(row.id),
                  payload
                );
                if (code === 0) {
                  message(`成功更新用户 ${curData.username}`, {
                    type: "success"
                  });
                  done();
                  onSearch();
                  return;
                }
              }
              // 业务失败（code !== 0）：提示并保持对话框打开供用户修正重试
              closeLoading();
              message(`${title}用户失败，请稍后重试`, { type: "error" });
            } catch {
              // 请求异常：同样保持对话框打开，并复位确定按钮 loading
              closeLoading();
              message(`${title}用户失败`, { type: "error" });
            }
          } else {
            // 表单校验未通过：复位确定按钮 loading，等待用户修正
            closeLoading();
          }
        });
      }
    });

    // 编辑时先开窗，再异步回填用户已分配的岗位，避免网络慢阻塞弹窗打开
    if (row?.id) {
      formLoading.value = true;
      try {
        formInline.postIds =
          (await postApi.userPosts(String(row.id)).catch(() => null))?.data ??
          [];
      } finally {
        formLoading.value = false;
      }
    }
  }

  const cropRef = ref();
  function handleUpload(row) {
    addDialog({
      title: "裁剪、上传头像",
      width: "40%",
      closeOnClickModal: false,
      fullscreen: deviceDetection(),
      contentRenderer: () =>
        h(ReCropperPreview, {
          ref: cropRef,
          imgSrc: row.avatar || userAvatar,
          onCropper: info => (avatarInfo.value = info)
        }),
      beforeSure: done => {
        done();
        onSearch();
      },
      closeCallBack: () => cropRef.value.hidePopover()
    });
  }

  // 密码强度计算（zxcvbn 较重）防抖 250ms：连续按键只计算最后一次输入
  watch(
    pwdForm,
    useDebounceFn(({ newPwd }) => {
      curScore.value = isAllEmpty(newPwd)
        ? -1
        : zxcvbnFactory.check(newPwd).score;
    }, 250)
  );

  function handleReset(row) {
    addDialog({
      title: `重置 ${row.username} 用户的密码`,
      // 弹窗宽度分档：简单单列表单 560px
      width: "560px",
      draggable: true,
      closeOnClickModal: false,
      fullscreen: deviceDetection(),
      contentRenderer: () => (
        <>
          <ElForm ref={ruleFormRef} model={pwdForm}>
            <ElFormItem
              prop="newPwd"
              rules={[
                {
                  required: true,
                  message: "请输入新密码",
                  trigger: "blur"
                }
              ]}
            >
              <ElInput
                clearable
                show-password
                type="password"
                v-model={pwdForm.newPwd}
                placeholder="请输入新密码"
              />
            </ElFormItem>
          </ElForm>
          <div class="my-4 flex">
            {pwdProgress.map(({ color, text }, idx) => (
              <div
                class="w-[19vw]"
                style={{ marginLeft: idx !== 0 ? "4px" : 0 }}
              >
                <ElProgress
                  striped
                  striped-flow
                  duration={curScore.value === idx ? 6 : 0}
                  percentage={curScore.value >= idx ? 100 : 0}
                  color={color}
                  stroke-width={10}
                  show-text={false}
                />
                <p
                  class="text-center"
                  style={{ color: curScore.value === idx ? color : "" }}
                >
                  {text}
                </p>
              </div>
            ))}
          </div>
        </>
      ),
      closeCallBack: () => (pwdForm.newPwd = ""),
      beforeSure: done => {
        ruleFormRef.value.validate(async valid => {
          if (valid) {
            try {
              const { code } = await userApi.resetPassword(row.id, {
                newPassword: pwdForm.newPwd
              });
              if (code === 0) {
                message(`已成功重置 ${row.username} 用户的密码`, {
                  type: "success"
                });
                done();
                onSearch();
              }
            } catch {
              message("重置密码失败", { type: "error" });
            }
          }
        });
      }
    });
  }

  function handleRole(row) {
    /** 表单区加载态：异步回填已分配角色期间遮罩表单 */
    const roleLoading = ref(false);
    /** reactive 传入 ReDialog：先同步开窗，角色异步回填后直接响应式更新表单 */
    const formInline = reactive<RoleFormItemProps>({
      username: row?.username ?? "",
      nickname: row?.nickname ?? "",
      roleOptions: roleOptions.value ?? [],
      ids: []
    });
    addDialog({
      title: `分配 ${row.username} 用户的角色`,
      props: {
        formInline
      },
      // 弹窗宽度分档：简单单列表单 560px
      width: "560px",
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      contentRenderer: () =>
        h(roleForm, { formInline: null, formLoading: roleLoading.value }),
      beforeSure: (done, { options }) => {
        const curData = options.props.formInline as RoleFormItemProps;
        (async () => {
          try {
            const { code } = await userApi.assignUserRole({
              userId: row.id,
              roleIds: curData.ids
            });
            if (code === 0) {
              message(`已成功为用户 ${row.username} 分配角色`, {
                type: "success"
              });
              done();
            }
          } catch {
            message("分配角色失败", { type: "error" });
          }
        })();
      }
    });

    // 先开窗，再异步回填用户已分配的角色，避免网络慢阻塞弹窗打开
    roleLoading.value = true;
    userApi
      .getRoleIds({ userId: row.id })
      .catch(() => null)
      .then(res => (formInline.ids = res?.data ?? []))
      .finally(() => (roleLoading.value = false));
  }

  /**
   * 单源加载失败收口：业务失败（4xx 等）本地提示，
   * 网络层错误（取消/断网/5xx）由全局拦截器统一提示，这里静默
   */
  function notifyLoadError(error: unknown, fallbackText: string) {
    if (!isNetworkLevelError(error)) {
      message(fallbackText, { type: "error" });
    }
  }

  /** 加载部门树下拉数据（业务失败本地提示，网络层错误静默） */
  async function loadHigherDeptOptions() {
    try {
      const { code, data } = await deptApi.listTree();
      if (code !== 0) {
        message("部门树加载失败", { type: "error" });
        return;
      }
      higherDeptOptions.value = handleTree(data);
    } catch (error) {
      notifyLoadError(error, "部门树加载失败");
    }
  }

  /** 加载角色下拉数据（业务失败本地提示，网络层错误静默） */
  async function loadRoleOptions() {
    try {
      const res = await userApi.getAllRoleList();
      if (res.code !== 0) {
        message("角色列表加载失败", { type: "error" });
        return;
      }
      roleOptions.value = res.data ?? [];
    } catch (error) {
      notifyLoadError(error, "角色列表加载失败");
    }
  }

  /** 加载岗位下拉数据（业务失败本地提示，网络层错误静默） */
  async function loadPostOptions() {
    try {
      const res = await postApi.options();
      if (res.code !== 0) {
        message("岗位选项加载失败", { type: "error" });
        return;
      }
      postOptions.value = res.data ?? [];
    } catch (error) {
      notifyLoadError(error, "岗位选项加载失败");
    }
  }

  // 组件卸载时取消进行中的搜索请求，防止卸载后仍回写状态
  onScopeDispose(() => {
    searchController?.abort();
  });

  onMounted(() => {
    onSearch();

    // 三个下拉数据源相互独立，Promise.allSettled 并行加载，任一失败不阻塞其余源与页面渲染
    void Promise.allSettled([
      loadHigherDeptOptions(),
      loadRoleOptions(),
      loadPostOptions()
    ]);
  });

  return {
    form,
    loading,
    columns,
    dataList,
    selectedNum,
    pagination,
    buttonClass,
    deviceDetection,
    onSearch,
    resetForm,
    onbatchDel,
    openDialog,
    handleUpdate,
    handleDelete,
    handleUpload,
    handleReset,
    handleRole,
    handleSizeChange,
    onSelectionCancel,
    handleCurrentChange,
    handleSelectionChange
  };
}
