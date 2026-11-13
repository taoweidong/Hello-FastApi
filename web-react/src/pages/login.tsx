import { Button, Card, Form, Input } from "antd";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { login } from "@/api/auth";
import { useAuthStore } from "@/store/auth";
import { bindMessage } from "@/api/client";
import { App } from "antd";

export default function LoginPage(): React.ReactNode {
  const navigate = useNavigate();
  const setLogin = useAuthStore(s => s.setLogin);
  const [loading, setLoading] = useState(false);
  const { message } = App.useApp();
  bindMessage(message);

  async function onFinish(values: { username: string; password: string }): Promise<void> {
    setLoading(true);
    try {
      const data = await login(values);
      setLogin(data);
      // 登录后拉取动态路由由布局组件完成；此处直接进首页
      navigate("/welcome", { replace: true });
    } catch {
      // 错误提示已由 axios 拦截器统一处理
    } finally {
      setLoading(false);
    }
  }

  return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #1677ff14, #7c3aed14)"
        }}
      >
        <Card title="PureAdmin React 管理端" style={{ width: 380 }}>
          <Form onFinish={onFinish} initialValues={{ username: "admin", password: "admin123" }} size="large">
            <Form.Item name="username" rules={[{ required: true, message: "请输入用户名" }]}>
              <Input prefix={<UserOutlined />} placeholder="用户名" autoFocus />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: "请输入密码" }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={loading}>
                登录
              </Button>
            </Form.Item>
          </Form>
      </Card>
    </div>
  );
}
