import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
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
  Space,
  Spin,
  Table,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';
import {
  downloadLogFile,
  getLogFiles,
  getServerInfo,
  type LogFile,
  type ServerInfo,
  tailLogFile,
} from '@/services/api';

type LogFileColumns = TableProps<LogFile>['columns'];

/** 字节大小转可读显示（B/KB/MB/GB，对齐 Vue formatSize） */
function formatSize(sizeBytes: number): string {
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let value = sizeBytes / 1024;
  let unitIdx = 0;
  while (value >= 1024 && unitIdx < units.length - 1) {
    value /= 1024;
    unitIdx += 1;
  }
  return `${value.toFixed(1)} ${units[unitIdx]}`;
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
  // 日志清单独立刷新态（对齐 Vue 刷新日志按钮）
  const [logsLoading, setLogsLoading] = useState(false);
  // 正在下载的日志文件名（防重复点击）
  const [downloading, setDownloading] = useState('');

  const fetchServerInfo = useCallback(async () => {
    try {
      setInfo(await getServerInfo());
    } catch (error) {
      message.error((error as Error).message || '获取服务器信息失败');
    }
  }, [message]);

  const fetchLogFiles = useCallback(async () => {
    if (!isAdmin) return;
    setLogsLoading(true);
    try {
      setLogFiles(await getLogFiles());
    } catch {
      // 非管理员/网络异常：清单留空，不阻塞监控主体
      setLogFiles([]);
    } finally {
      setLogsLoading(false);
    }
  }, [isAdmin]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([fetchServerInfo(), fetchLogFiles()]);
    } finally {
      setLoading(false);
    }
  }, [fetchLogFiles, fetchServerInfo]);

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
      const tail = await tailLogFile(record.name, 200);
      setTailContent(tail.content);
    } catch (error) {
      setTailContent(`读取日志失败：${(error as Error).message}`);
    } finally {
      setTailLoading(false);
    }
  }

  /** 重新读取当前弹窗中的日志尾部（不关闭弹窗） */
  async function refreshTail(): Promise<void> {
    if (!tailFile) return;
    setTailLoading(true);
    try {
      const tail = await tailLogFile(tailFile, 200);
      setTailContent(tail.content);
    } catch (error) {
      setTailContent(`读取日志失败：${(error as Error).message}`);
    } finally {
      setTailLoading(false);
    }
  }

  /** 下载日志文件：blob → objectURL → a.download 触发保存 → revoke */
  async function handleDownload(record: LogFile): Promise<void> {
    setDownloading(record.name);
    try {
      const blob = await downloadLogFile(record.name);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = record.name;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      message.error(
        `${(error as Error).message || '下载失败'}（下载失败：需要管理员权限）`,
      );
    } finally {
      setDownloading('');
    }
  }

  const logColumns: LogFileColumns = [
    { title: '文件名', dataIndex: 'name', key: 'name' },
    {
      title: '大小',
      dataIndex: 'sizeBytes',
      key: 'sizeBytes',
      width: 120,
      render: (value: number) => formatSize(value),
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
      width: 180,
      render: (_, record) => (
        <Space size={4}>
          <Button
            type="link"
            size="small"
            onClick={() => void openTail(record)}
          >
            查看尾部
          </Button>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            loading={downloading === record.name}
            onClick={() => void handleDownload(record)}
          >
            下载
          </Button>
        </Space>
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
        <Card
          title="日志文件"
          style={{ marginTop: 16 }}
          extra={
            <Button
              icon={<ReloadOutlined />}
              size="small"
              loading={logsLoading}
              onClick={() => void fetchLogFiles()}
            >
              刷新日志
            </Button>
          }
        >
          <Table<LogFile>
            rowKey="name"
            size="small"
            columns={logColumns}
            dataSource={logFiles}
            pagination={false}
            loading={logsLoading && logFiles.length === 0 && loading}
          />
        </Card>
      )}

      <Modal
        title={`日志尾部：${tailFile}`}
        open={tailOpen}
        width={860}
        onCancel={() => setTailOpen(false)}
        footer={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              loading={tailLoading}
              onClick={() => void refreshTail()}
            >
              重新读取
            </Button>
            <Button onClick={() => setTailOpen(false)}>关闭</Button>
          </Space>
        }
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
          {tailLoading ? '加载中...' : tailContent || '（空文件）'}
        </pre>
      </Modal>
    </div>
  );
}
