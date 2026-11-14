import { ReloadOutlined } from '@ant-design/icons';
import { useModel } from '@umijs/max';
import type { TableProps } from 'antd';
import {
  Alert,
  App,
  Button,
  Card,
  Col,
  Descriptions,
  Popconfirm,
  Row,
  Spin,
  Table,
  Tag,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';
import {
  type CacheCommandStat,
  type CacheGroup,
  type CacheInfo,
  clearAllCache,
  clearCacheGroup,
  getCacheGroups,
  getCacheInfo,
} from '@/services/api';

type CommandStatColumns = TableProps<CacheCommandStat>['columns'];

/** 运行时长（秒）转人性化文本 */
function formatUptime(seconds?: number): string {
  if (seconds === undefined || seconds === null) {
    return '-';
  }
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) {
    return `${days}天${hours}小时${minutes}分`;
  }
  if (hours > 0) {
    return `${hours}小时${minutes}分`;
  }
  return `${minutes}分`;
}

/** 命令调用统计（Top10）表格列 */
const commandStatColumns: CommandStatColumns = [
  { title: '命令', dataIndex: 'name', key: 'name' },
  { title: '调用次数', dataIndex: 'calls', key: 'calls', width: 140 },
  {
    title: '累计耗时（微秒）',
    dataIndex: 'usec',
    key: 'usec',
    width: 180,
  },
];

/** 缓存监控：Redis 运行状态 + 缓存分组（清理操作仅管理员） */
export default function CachePage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const isAdmin =
    initialState?.permissions?.includes('monitor:manage') ?? false;

  const [info, setInfo] = useState<CacheInfo | null>(null);
  const [groups, setGroups] = useState<CacheGroup[]>([]);
  const [loading, setLoading] = useState(true);
  // 正在清理的分组 key；'__all__' 表示清空全部
  const [clearingKey, setClearingKey] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [cacheInfo, cacheGroupList] = await Promise.all([
        getCacheInfo(),
        getCacheGroups(),
      ]);
      setInfo(cacheInfo);
      setGroups(cacheGroupList);
    } catch (error) {
      message.error((error as Error).message || '获取缓存信息失败');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  async function handleClearGroup(group: CacheGroup): Promise<void> {
    setClearingKey(group.key);
    try {
      const count = await clearCacheGroup(group.key);
      message.success(`已清理「${group.name}」分组 ${count} 个键`);
      await fetchData();
    } catch (error) {
      message.error((error as Error).message || '清理缓存失败');
    } finally {
      setClearingKey('');
    }
  }

  async function handleClearAll(): Promise<void> {
    setClearingKey('__all__');
    try {
      const count = await clearAllCache();
      message.success(`已清空全部缓存 ${count} 个键`);
      await fetchData();
    } catch (error) {
      message.error((error as Error).message || '清空缓存失败');
    } finally {
      setClearingKey('');
    }
  }

  if (loading && !info) {
    return (
      <Spin
        style={{ display: 'flex', justifyContent: 'center', padding: 100 }}
      />
    );
  }

  const statusItems = [
    { key: 'version', label: '版本', children: info?.version ?? '-' },
    { key: 'mode', label: '模式', children: info?.mode ?? '-' },
    {
      key: 'uptime',
      label: '运行时长',
      children: formatUptime(info?.uptimeSeconds),
    },
    { key: 'usedMemory', label: '已用内存', children: info?.usedMemory ?? '-' },
    {
      key: 'usedMemoryPeak',
      label: '内存峰值',
      children: info?.usedMemoryPeak ?? '-',
    },
    {
      key: 'clients',
      label: '连接数',
      children: info ? String(info.clients ?? '-') : '-',
    },
    {
      key: 'keyCount',
      label: '键总数',
      children: info ? String(info.keyCount ?? '-') : '-',
    },
    {
      key: 'hitRate',
      label: '命中率',
      children: info ? `${info.hitRate ?? '-'}%` : '-',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="Redis 运行状态"
        extra={
          <span
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}
          >
            {info?.connected ? (
              <Tag color="green">连接正常</Tag>
            ) : (
              <Tag color="red">缓存服务不可用</Tag>
            )}
            <Button
              icon={<ReloadOutlined />}
              loading={loading}
              onClick={() => void fetchData()}
            >
              刷新
            </Button>
          </span>
        }
      >
        {info?.connected ? (
          <>
            <Descriptions
              column={{ xs: 1, md: 2, lg: 4 }}
              size="small"
              items={statusItems}
            />
            {(info.commandStats?.length ?? 0) > 0 && (
              <>
                <div style={{ margin: '16px 0 8px', fontWeight: 600 }}>
                  命令调用统计（Top10）
                </div>
                <Table<CacheCommandStat>
                  rowKey="name"
                  size="small"
                  bordered
                  columns={commandStatColumns}
                  dataSource={info.commandStats}
                  pagination={false}
                />
              </>
            )}
          </>
        ) : (
          <div style={{ color: 'rgba(0, 0, 0, 0.45)' }}>
            {info?.message || 'Redis 连接不可用，无法读取缓存状态。'}
          </div>
        )}
      </Card>

      <Card
        title="缓存数据分组"
        style={{ marginTop: 16 }}
        extra={
          isAdmin &&
          groups.some((g) => g.clearable) && (
            <Popconfirm
              title="确定清空全部缓存吗？"
              description="将清空全部可清理业务缓存（不含令牌黑名单与限流键），确认继续？"
              onConfirm={() => void handleClearAll()}
            >
              <Button danger loading={clearingKey === '__all__'}>
                清空全部缓存
              </Button>
            </Popconfirm>
          )
        }
      >
        <Alert
          style={{ marginBottom: 16 }}
          type="info"
          showIcon
          message="清理缓存后相关数据将回源数据库重建；令牌黑名单为安全数据不可清理。"
        />
        {groups.length === 0 ? (
          <div style={{ color: 'rgba(0, 0, 0, 0.45)' }}>暂无缓存分组数据</div>
        ) : (
          <Row gutter={[16, 16]}>
            {groups.map((group) => (
              <Col xs={24} sm={12} lg={8} key={group.key}>
                <Card
                  size="small"
                  title={group.name}
                  extra={
                    isAdmin &&
                    (group.clearable ? (
                      <Popconfirm
                        title={`确定清理「${group.name}」分组吗？`}
                        description={`将删除该分组全部 ${group.count} 个缓存键`}
                        onConfirm={() => void handleClearGroup(group)}
                      >
                        <Button
                          size="small"
                          type="link"
                          danger
                          loading={clearingKey === group.key}
                        >
                          快速清理
                        </Button>
                      </Popconfirm>
                    ) : (
                      <span
                        style={{ fontSize: 12, color: 'rgba(0, 0, 0, 0.45)' }}
                      >
                        安全数据，不可清理
                      </span>
                    ))
                  }
                >
                  <div>
                    键前缀：<code>{group.prefix || '-'}*</code>
                  </div>
                  <div>键数量：{group.count}</div>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Card>
    </div>
  );
}
