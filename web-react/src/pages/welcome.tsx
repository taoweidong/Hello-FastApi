import { Card, Col, Progress, Row, Spin, Statistic } from 'antd';
import { useEffect, useState } from 'react';

/** 首页：复用后端 /server-info 展示服务器状态 */
export default function WelcomePage(): React.ReactNode {
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/system/server-info')
      .then((res) => res.json())
      .then((body) => {
        if (body.code === 0) setInfo(body.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <Spin
        style={{ display: 'flex', justifyContent: 'center', padding: 100 }}
      />
    );

  return (
    <Row gutter={16} style={{ padding: 24 }}>
      <Col span={8}>
        <Card size="small" title="CPU">
          <Progress
            type="dashboard"
            percent={Math.round(
              (info?.cpu as Record<string, number>)?.usedPercent ?? 0,
            )}
          />
        </Card>
      </Col>
      <Col span={8}>
        <Card size="small" title="内存">
          <Progress
            type="dashboard"
            percent={Math.round(
              (info?.memory as Record<string, number>)?.usedPercent ?? 0,
            )}
          />
        </Card>
      </Col>
      <Col span={8}>
        <Card size="small" title="磁盘">
          <Progress
            type="dashboard"
            percent={Math.round(
              (info?.disk as Record<string, number>)?.usedPercent ?? 0,
            )}
          />
        </Card>
      </Col>
    </Row>
  );
}
