import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { LoginForm, ProFormText } from '@ant-design/pro-components';
import { history, useModel } from '@umijs/max';
import { Button, message } from 'antd';
import { useState } from 'react';
import { getAsyncRoutes, type MineInfo } from '@/services/api';
import { realtime } from '@/utils/websocket';
import Settings from '../../../../config/defaultSettings';

/** 登录页：调用 Hello-FastApi 后端 /api/system/login */
export default function LoginPage(): React.ReactNode {
  const { initialState, setInitialState } = useModel('@@initialState');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(values: {
    username: string;
    password: string;
  }): Promise<void> {
    setLoading(true);
    try {
      const res = await fetch('/api/system/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      const body = await res.json();
      if (body.code !== 0) {
        message.error(body.message || '登录失败');
        return;
      }
      // 存储令牌到 localStorage（app.tsx 的请求拦截器会读取；expires 用于令牌续期）
      localStorage.setItem(
        'react-admin-auth',
        JSON.stringify({
          state: {
            accessToken: body.data.accessToken,
            refreshToken: body.data.refreshToken,
            expires: body.data.expires,
            username: body.data.username,
            nickname: body.data.nickname,
            avatar: body.data.avatar,
            permissions: body.data.permissions,
          },
        }),
      );
      // SPA 登录：刷新 initialState（用户信息 + 权限码 + 动态菜单）并建立实时通道
      try {
        const routes = await getAsyncRoutes();
        const mine: MineInfo = {
          username: body.data.username,
          nickname: body.data.nickname,
          avatar: body.data.avatar,
          email: '',
          phone: '',
        };
        setInitialState((s) => ({
          ...s,
          currentUser: mine,
          permissions: body.data.permissions,
          menus: routes,
          settings: Settings as never,
        }));
      } catch {
        /* 动态菜单拉取失败时回退到整页刷新路径 */
        window.location.href = '/welcome';
        return;
      }
      realtime.start();
      history.push('/welcome');
    } catch {
      message.error('网络错误');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1677ff14, #7c3aed14)',
      }}
    >
      <LoginForm
        title="PureAdmin React"
        subTitle="Hello-FastApi React 管理端"
        logo="https://pure-admin.github.io/vue-pure-admin/logo.svg"
        onFinish={async (values) =>
          handleSubmit(values as { username: string; password: string })
        }
      >
        <ProFormText
          name="username"
          fieldProps={{ size: 'large', prefix: <UserOutlined /> }}
          placeholder="用户名：admin"
          rules={[{ required: true, message: '请输入用户名' }]}
        />
        <ProFormText.Password
          name="password"
          fieldProps={{ size: 'large', prefix: <LockOutlined /> }}
          placeholder="密码：admin123"
          rules={[{ required: true, message: '请输入密码' }]}
        />
        <div style={{ marginBottom: 24 }}>
          <Button
            type="primary"
            htmlType="submit"
            block
            size="large"
            loading={loading}
          >
            登录
          </Button>
        </div>
      </LoginForm>
    </div>
  );
}
