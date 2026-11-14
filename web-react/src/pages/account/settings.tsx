import type { TableProps } from 'antd';
import { App, Button, Card, Col, Form, Input, Row, Table, Tag } from 'antd';
import { useCallback, useEffect, useState } from 'react';
import {
  changePassword,
  getMine,
  getMineLogs,
  type MineInfo,
  type MineLogRow,
  updateProfile,
} from '@/services/api';

type MineLogColumns = TableProps<MineLogRow>['columns'];

/** 个人中心：个人信息 / 修改密码 / 安全日志 */
export default function SettingsPage(): React.ReactNode {
  const { message } = App.useApp();
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const [mine, setMine] = useState<MineInfo | null>(null);
  const [profileSaving, setProfileSaving] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);

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
  }): Promise<void> {
    setProfileSaving(true);
    try {
      await updateProfile(values);
      message.success('个人信息已保存');
      const data = await getMine();
      setMine(data);
    } catch (error) {
      message.error((error as Error).message || '保存个人信息失败');
    } finally {
      setProfileSaving(false);
    }
  }

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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (_, record) => (
        <Tag color={record.status === 1 ? 'green' : 'red'}>
          {record.status === 1 ? '成功' : '失败'}
        </Tag>
      ),
    },
    { title: 'IP地址', dataIndex: 'ipaddress', key: 'ipaddress' },
    { title: '浏览器', dataIndex: 'browser', key: 'browser' },
    { title: '时间', dataIndex: 'createdTime', key: 'createdTime' },
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
              <Form.Item style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={profileSaving}
                >
                  保存
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
                label="原密码"
                name="oldPassword"
                rules={[{ required: true, message: '请输入原密码' }]}
              >
                <Input.Password
                  placeholder="请输入原密码"
                  autoComplete="old-password"
                />
              </Form.Item>
              <Form.Item
                label="新密码"
                name="newPassword"
                rules={[
                  { required: true, message: '请输入新密码' },
                  { min: 6, message: '新密码长度不能少于 6 位' },
                ]}
              >
                <Input.Password
                  placeholder="请输入新密码"
                  autoComplete="new-password"
                />
              </Form.Item>
              <Form.Item style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={passwordSaving}
                >
                  保存
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
