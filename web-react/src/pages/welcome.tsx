import { Card, Col, Progress, Row, Spin, Statistic } from "antd";
import { useQuery } from "@tanstack/react-query";
import { http } from "@/api/client";

interface ServerInfo {
  cpu: { coreCount: number; usedPercent: number };
  memory: { total: string; used: string; free: string; usedPercent: number };
  disk: { total: string; used: string; free: string; usedPercent: number };
  system: {
    hostname: string;
    osName: string;
    osArch: string;
    pythonVersion: string;
    workDir: string;
    bootTime: string;
  };
}

/** 首页：复用后端 /server-info 展示服务器状态 */
export default function WelcomePage(): React.ReactNode {
  const { data, isLoading } = useQuery({
    queryKey: ["server-info"],
    queryFn: async () => {
      const res = await http.get<{ code: number; data: ServerInfo }>("/server-info");
      return res.data.data;
    }
  });

  return (
    <Card title="首页 · 服务器状态">
      {isLoading || !data ? (
        <Spin />
      ) : (
        <>
          <Row gutter={16}>
            <Col span={8}>
              <Card size="small">
                <Statistic title="CPU 使用率" value={data.cpu.usedPercent} suffix="%" precision={1} />
                <Progress percent={Math.round(data.cpu.usedPercent)} size="small" />
                <div style={{ color: "#999" }}>逻辑核心：{data.cpu.coreCount}</div>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic title="内存使用率" value={data.memory.usedPercent} suffix="%" precision={1} />
                <Progress percent={Math.round(data.memory.usedPercent)} size="small" />
                <div style={{ color: "#999" }}>
                  已用 {data.memory.used} / 总量 {data.memory.total}
                </div>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic title="磁盘使用率" value={data.disk.usedPercent} suffix="%" precision={1} />
                <Progress percent={Math.round(data.disk.usedPercent)} size="small" />
                <div style={{ color: "#999" }}>
                  已用 {data.disk.used} / 总量 {data.disk.total}
                </div>
              </Card>
            </Col>
          </Row>
          <Card size="small" title="系统信息" style={{ marginTop: 16 }}>
            <Statistic title="操作系统" value={data.system.osName} valueStyle={{ fontSize: 14 }} />
            <Statistic title="主机名" value={data.system.hostname} valueStyle={{ fontSize: 14 }} />
            <Statistic title="Python 版本" value={data.system.pythonVersion} valueStyle={{ fontSize: 14 }} />
            <Statistic title="启动时间" value={data.system.bootTime.replace("T", " ").slice(0, 19)} valueStyle={{ fontSize: 14 }} />
          </Card>
        </>
      )}
    </Card>
  );
}
