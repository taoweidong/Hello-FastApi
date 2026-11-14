import { UserOutlined } from '@ant-design/icons';
import { useModel } from '@umijs/max';
import type { TableProps, UploadProps } from 'antd';
import {
  App,
  Avatar,
  Button,
  Card,
  Col,
  Form,
  Input,
  Row,
  Table,
  Tag,
  Upload,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';
import {
  changePassword,
  getMine,
  getMineLogs,
  type MineInfo,
  type MineLogRow,
  updateProfile,
  uploadAvatar,
} from '@/services/api';

type MineLogColumns = TableProps<MineLogRow>['columns'];

/** 头像限制（与后端一致：仅图片，≤2MB） */
const MAX_AVATAR_MB = 2;

/** 个人中心：个人信息（头像上传/简介）/ 修改密码 / 安全日志 */
export default function SettingsPage(): React.ReactNode {
  const { message } = App.useApp();
  const { setInitialState } = useModel('@@initialState');
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const [mine, setMine] = useState<MineInfo | null>(null);
  const [profileSaving, setProfileSaving] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);

  // 安全日志分页状态（只读列表）
  const [logs, setLogs] = useState<MineLogRow[]>([]);
  const [logTotal, setLogTotal] = useState(0);
  const [logPage, setLogPage] = useState(1);
  const [logPageSize, setLogPageSize] = useState(10);
  const [logLoading, setLogLoading] = useState(false);

  const loadLogs = useCallback(
    async (page: number, pageSize: number) => {
      setLogLoading(true);
      try {
        const data = await getMineLogs({ pageNum: page, pageSize });
        setLogs(data.list);
        setLogTotal(data.total);
      } catch (error) {
        message.error((error as Error).message || '获取安全日志失败');
      } finally {
        setLogLoading(false);
      }
    },
    [message],
  );

  useEffect(() => {
    void loadLogs(logPage, logPageSize);
  }, [loadLogs, logPage, logPageSize]);

  useEffect(() => {
    getMine()
      .then((data) => {
        setMine(data);
        profileForm.setFieldsValue({
          nickname: data.nickname,
          email: data.email,
          phone: data.phone,
          description: data.description ?? '',
        });
      })
      .catch(() => {
        // 获取失败保持表单为空，错误提示由拦截器统一处理
      });
  }, [profileForm]);

  async function handleProfileSave(values: {
    nickname?: string;
    email?: string;
    phone?: string;
    description?: string;
  }): Promise<void> {
    setProfileSaving(true);
    try {
      await updateProfile({
        ...values,
        email: values.email || null,
        phone: values.phone || null,
        description: values.description || null,
      });
      message.success('个人信息已保存');
      const data = await getMine();
      setMine(data);
      // 同步顶栏头像/昵称（全局 initialState）
      setInitialState((prev) => ({
        ...prev,
        currentUser: prev?.currentUser
          ? { ...prev.currentUser, ...data }
          : prev?.currentUser,
      }));
    } catch (error) {
      message.error((error as Error).message || '保存个人信息失败');
    } finally {
      setProfileSaving(false);
    }
  }

  /** 头像上传前校验：仅图片、≤2MB（对齐后端约束） */
  const beforeAvatarUpload: UploadProps['beforeUpload'] = (file) => {
    const isImage = /^image\//.test(file.type);
    if (!isImage) {
      message.error('仅支持 jpg/jpeg/png/gif/webp 格式的图片');
      return Upload.LIST_IGNORE;
    }
    if (file.size / 1024 / 1024 > MAX_AVATAR_MB) {
      message.error('头像文件大小不能超过 2MB');
      return Upload.LIST_IGNORE;
    }
    return true;
  };

  /** 自定义上传：FormData 字段名 file → POST /user/avatar → 刷新全局 currentUser */
  const handleAvatarRequest: UploadProps['customRequest'] = (options) => {
    const formData = new FormData();
    formData.append('file', options.file as File);
    setAvatarUploading(true);
    uploadAvatar(formData)
      .then(({ avatar }) => {
        message.success('更新头像成功');
        setMine((prev) => (prev ? { ...prev, avatar } : prev));
        setInitialState((prev) => ({
          ...prev,
          currentUser: prev?.currentUser
            ? { ...prev.currentUser, avatar }
            : prev?.currentUser,
        }));
        options.onSuccess?.(avatar);
      })
      .catch((error: unknown) => {
        message.error((error as Error)?.message || '提交异常，头像更新失败');
        options.onError?.(error as Error);
      })
      .finally(() => {
        setAvatarUploading(false);
      });
  };

  async function handlePasswordSave(values: {
    oldPassword: string;
    newPassword: string;
  }): Promise<void> {
    setPasswordSaving(true);
    try {
      await changePassword({
        oldPassword: values.oldPassword,
        newPassword: values.newPassword,
      });
      message.success('密码修改成功');
      passwordForm.resetFields();
    } catch (error) {
      message.error((error as Error).message || '修改密码失败');
    } finally {
      setPasswordSaving(false);
    }
  }

  const logColumns: MineLogColumns = [
    {
      title: '登录状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (_, record) => (
        <Tag color={record.status === 1 ? 'green' : 'red'}>
          {record.status === 1 ? '登录成功' : '登录失败'}
        </Tag>
      ),
    },
    { title: 'IP 地址', dataIndex: 'ip', key: 'ip' },
    { title: '操作系统', dataIndex: 'system', key: 'system' },
    { title: '浏览器类型', dataIndex: 'browser', key: 'browser' },
    {
      title: '时间',
      dataIndex: 'loginTime',
      key: 'loginTime',
      width: 170,
      render: (_, record) => record.loginTime ?? '-',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title={mine ? `个人信息（${mine.username}）` : '个人信息'}>
            <Form
              form={profileForm}
              layout="vertical"
              onFinish={handleProfileSave}
            >
              <Form.Item label="头像">
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <Avatar
                    size={80}
                    src={mine?.avatar || undefined}
                    icon={<UserOutlined />}
                  />
                  <Upload
                    accept="image/*"
                    showUploadList={false}
                    maxCount={1}
                    beforeUpload={beforeAvatarUpload}
                    customRequest={handleAvatarRequest}
                  >
                    <Button loading={avatarUploading}>更新头像</Button>
                  </Upload>
                </div>
              </Form.Item>
              <Form.Item
                label="昵称"
                name="nickname"
                rules={[{ required: true, message: '请输入昵称' }]}
              >
                <Input placeholder="请输入昵称" />
              </Form.Item>
              <Form.Item
                label="邮箱"
                name="email"
                rules={[{ type: 'email', message: '邮箱格式不正确' }]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
              <Form.Item label="手机号" name="phone">
                <Input placeholder="请输入手机号" />
              </Form.Item>
              <Form.Item
                label="简介"
                name="description"
                rules={[{ max: 56, message: '简介最多 56 个字符' }]}
              >
                <Input.TextArea
                  rows={4}
                  maxLength={56}
                  showCount
                  placeholder="请输入简介"
                />
              </Form.Item>
              <Form.Item style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={profileSaving}
                >
                  更新信息
                </Button>
              </Form.Item>
            </Form>
          </Card>

          <Card title="修改密码" style={{ marginTop: 16 }}>
            <Form
              form={passwordForm}
              layout="vertical"
              onFinish={handlePasswordSave}
            >
              <Form.Item
                label="当前密码"
                name="oldPassword"
                rules={[{ required: true, message: '当前密码为必填项' }]}
              >
                <Input.Password
                  placeholder="请输入当前密码"
                  autoComplete="old-password"
                />
              </Form.Item>
              <Form.Item
                label="新密码"
                name="newPassword"
                rules={[
                  { required: true, message: '新密码为必填项' },
                  { min: 8, message: '密码长度至少 8 位' },
                ]}
              >
                <Input.Password
                  placeholder="至少 8 位"
                  autoComplete="new-password"
                />
              </Form.Item>
              <Form.Item style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={passwordSaving}
                >
                  确定
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="安全日志">
            <Table<MineLogRow>
              rowKey="id"
              size="small"
              columns={logColumns}
              dataSource={logs}
              loading={logLoading}
              pagination={{
                current: logPage,
                pageSize: logPageSize,
                total: logTotal,
                showSizeChanger: true,
                onChange: (page, pageSize) => {
                  setLogPage(page);
                  setLogPageSize(pageSize);
                },
              }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
