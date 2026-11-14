import { ReloadOutlined } from '@ant-design/icons';
import { useModel } from '@umijs/max';
import type { TableProps } from 'antd';
import {
  App,
  Button,
  Card,
  Col,
  Descriptions,
  Modal,
  Progress,
  Row,
  Spin,
  Table,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';
import {
  getLogFiles,
  getServerInfo,
  type LogFile,
  type ServerInfo,
  tailLogFile,
} from '@/services/api';

type LogFileColumns = TableProps<LogFile>['columns'];

/** 字节大小转 KB 显示 */
function formatSizeKb(sizeBytes: number): string {
  return `${(sizeBytes / 1024).toFixed(1)} KB`;
}

interface StatItem {
  label: string;
  value: string;
}

/** CPU / 内存 / 磁盘共用的仪表盘卡片：Progress dashboard + 统计数据 */
function ResourceCard(props: {
  title: string;
  percent: number;
  stats: StatItem[];
}): React.ReactNode {
  const { title, percent, stats } = props;
  const percentValue = Math.max(0, Math.min(100, Math.round(percent)));
  return (
    <Card size="small" title={title}>
      <div style={{ textAlign: 'center' }}>
        <Progress
          type="dashboard"
          percent={percentValue}
          status={percentValue >= 90 ? 'exception' : 'normal'}
        />
      </div>
      <Descriptions
        size="small"
        column={1}
        style={{ marginTop: 8 }}
        items={stats.map((item) => ({
          key: item.label,
          label: item.label,
          children: item.value,
        }))}
      />
    </Card>
  );
}

/** 服务器监控：CPU / 内存 / 磁盘仪表盘 + 系统/进程信息 + 日志文件（仅管理员） */
export default function ServerPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const isAdmin =
    initialState?.permissions?.includes('monitor:manage') ?? false;

  const [info, setInfo] = useState<ServerInfo | null>(null);
  const [logFiles, setLogFiles] = useState<LogFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // 日志尾部查看弹窗状态
  const [tailOpen, setTailOpen] = useState(false);
  const [tailLoading, setTailLoading] = useState(false);
  const [tailFile, setTailFile] = useState('');
  const [tailContent, setTailContent] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const server = await getServerInfo();
      setInfo(server);
      if (isAdmin) {
        setLogFiles(await getLogFiles());
      }
    } catch (error) {
      message.error((error as Error).message || '获取服务器信息失败');
    } finally {
      setLoading(false);
    }
  }, [isAdmin, message]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  async function handleRefresh(): Promise<void> {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }

  async function openTail(record: LogFile): Promise<void> {
    setTailFile(record.name);
    setTailContent('');
    setTailOpen(true);
    setTailLoading(true);
    try {
      setTailContent(await tailLogFile(record.name, 200));
    } catch (error) {
      setTailContent(`读取日志失败：${(error as Error).message}`);
    } finally {
      setTailLoading(false);
    }
  }

  const logColumns: LogFileColumns = [
    { title: '文件名', dataIndex: 'name', key: 'name' },
    {
      title: '大小',
      dataIndex: 'sizeBytes',
      key: 'sizeBytes',
      width: 120,
      render: (value: number) => formatSizeKb(value),
    },
    {
      title: '修改时间',
      dataIndex: 'modifiedTime',
      key: 'modifiedTime',
      width: 200,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => void openTail(record)}>
          查看尾部
        </Button>
      ),
    },
  ];

  if (loading && !info) {
    return (
      <Spin
        style={{ display: 'flex', justifyContent: 'center', padding: 100 }}
      />
    );
  }

  const systemItems = [
    { key: 'osName', label: '操作系统', children: info?.system.osName ?? '-' },
    {
      key: 'hostname',
      label: '主机名',
      children: info?.system.hostname ?? '-',
    },
    { key: 'osArch', label: '系统架构', children: info?.system.osArch ?? '-' },
    {
      key: 'pythonVersion',
      label: 'Python 版本',
      children: info?.system.pythonVersion ?? '-',
    },
    {
      key: 'workDir',
      label: '工作目录',
      children: info?.system.workDir ?? '-',
    },
    {
      key: 'bootTime',
      label: '启动时间',
      children: info?.system.bootTime ?? '-',
    },
  ];

  const processItems = [
    {
      key: 'pid',
      label: 'PID',
      children: info ? String(info.process.pid) : '-',
    },
    {
      key: 'memoryUsed',
      label: '内存占用',
      children: info?.process.memoryUsed ?? '-',
    },
    {
      key: 'cpuPercent',
      label: 'CPU 占用',
      children: info ? `${info.process.cpuPercent}%` : '-',
    },
    {
      key: 'runningTime',
      label: '运行时长',
      children: info?.process.runningTime ?? '-',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <ResourceCard
            title={`CPU（${info?.cpu.coreCount ?? 0} 核）`}
            percent={info?.cpu.usedPercent ?? 0}
            stats={[
              { label: '核心数', value: String(info?.cpu.coreCount ?? 0) },
              { label: '使用率', value: `${info?.cpu.usedPercent ?? 0}%` },
            ]}
          />
        </Col>
        <Col xs={24} md={8}>
          <ResourceCard
            title="内存"
            percent={info?.memory.usedPercent ?? 0}
            stats={[
              { label: '总内存', value: info?.memory.total ?? '-' },
              { label: '已用', value: info?.memory.used ?? '-' },
              { label: '空闲', value: info?.memory.free ?? '-' },
            ]}
          />
        </Col>
        <Col xs={24} md={8}>
          <ResourceCard
            title="磁盘"
            percent={info?.disk.usedPercent ?? 0}
            stats={[
              { label: '总容量', value: info?.disk.total ?? '-' },
              { label: '已用', value: info?.disk.used ?? '-' },
              { label: '空闲', value: info?.disk.free ?? '-' },
            ]}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card
            title="系统信息"
            extra={
              <Button
                icon={<ReloadOutlined />}
                loading={refreshing}
                onClick={() => void handleRefresh()}
              >
                刷新
              </Button>
            }
          >
            <Descriptions column={2} size="small" items={systemItems} />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="进程信息">
            <Descriptions column={2} size="small" items={processItems} />
          </Card>
        </Col>
      </Row>

      {isAdmin && (
        <Card title="日志文件" style={{ marginTop: 16 }}>
          <Table<LogFile>
            rowKey="name"
            size="small"
            columns={logColumns}
            dataSource={logFiles}
            pagination={false}
            loading={loading}
          />
        </Card>
      )}

      <Modal
        title={`日志尾部：${tailFile}`}
        open={tailOpen}
        width={860}
        onCancel={() => setTailOpen(false)}
        footer={<Button onClick={() => setTailOpen(false)}>关闭</Button>}
      >
        <pre
          style={{
            maxHeight: 480,
            overflow: 'auto',
            margin: 0,
            padding: 12,
            background: 'rgba(0, 0, 0, 0.02)',
            border: '1px solid #f0f0f0',
            borderRadius: 6,
            fontSize: 12,
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {tailLoading ? '加载中...' : tailContent}
        </pre>
      </Modal>
    </div>
  );
}
