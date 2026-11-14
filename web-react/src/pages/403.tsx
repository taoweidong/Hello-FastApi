import { history } from '@umijs/max';
import { Button, Result } from 'antd';

/** 403 无权限访问（对齐 Vue /access-denied：返回首页按钮） */
export default function ForbiddenPage(): React.ReactNode {
  return (
    <Result
      status="403"
      title="403"
      subTitle="抱歉，你无权访问该页面"
      extra={
        <Button type="primary" onClick={() => history.replace('/')}>
          返回首页
        </Button>
      }
    />
  );
}
