import { history } from '@umijs/max';
import { Button, Result } from 'antd';

/** 500 服务器错误（对齐 Vue /server-error：返回首页按钮） */
export default function ServerErrorPage(): React.ReactNode {
  return (
    <Result
      status="500"
      title="500"
      subTitle="抱歉，服务器出错了"
      extra={
        <Button type="primary" onClick={() => history.replace('/')}>
          返回首页
        </Button>
      }
    />
  );
}
