import { Column, Line } from '@ant-design/plots';
import {
  Card,
  Col,
  Progress,
  Row,
  Segmented,
  Statistic,
  Table,
  Timeline,
} from 'antd';
import { useMemo, useState } from 'react';

/** 数据卡片静态数据（对齐 Vue web/src/views/welcome/data.ts） */
interface StatCard {
  name: string;
  value: number;
  percent: string;
  color: string;
  bgColor: string;
  data: Array<{ day: string; value: number }>;
}

const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

const CHART_DATA: StatCard[] = [
  {
    name: '需求人数',
    value: 36000,
    percent: '+88%',
    color: '#41b6ff',
    bgColor: '#effaff',
    data: [2101, 5288, 4239, 4962, 6752, 5208, 7450].map((value, i) => ({
      day: DAYS[i],
      value,
    })),
  },
  {
    name: '提问数量',
    value: 16580,
    percent: '+70%',
    color: '#e85f33',
    bgColor: '#fff5f4',
    data: [2216, 1148, 1255, 788, 4821, 1973, 4379].map((value, i) => ({
      day: DAYS[i],
      value,
    })),
  },
  {
    name: '解决数量',
    value: 16499,
    percent: '+99%',
    color: '#26ce83',
    bgColor: '#eff8f4',
    data: [861, 1002, 3195, 1715, 3666, 2415, 3645].map((value, i) => ({
      day: DAYS[i],
      value,
    })),
  },
  {
    name: '用户满意度',
    value: 100,
    percent: '+100%',
    color: '#7846e5',
    bgColor: '#f6f4fe',
    data: [{ day: DAYS[0], value: 100 }],
  },
];

/** 分析概览（上周/本周） */
const BAR_CHART_DATA = [
  {
    requireData: [2101, 5288, 4239, 4962, 6752, 5208, 7450],
    questionData: [2216, 1148, 1255, 1788, 4821, 1973, 4379],
  },
  {
    requireData: [2101, 3280, 4400, 4962, 5752, 6889, 7600],
    questionData: [2116, 3148, 3255, 3788, 4821, 4970, 5390],
  },
];

/** 解决概率（由周日到周一展示，对齐 Vue 顺序） */
const PROGRESS_DATA = [
  { week: '周日', percentage: 100, color: '#26ce83' },
  { week: '周六', percentage: 96, color: '#26ce83' },
  { week: '周五', percentage: 94, color: '#26ce83' },
  { week: '周四', percentage: 89, color: '#41b6ff' },
  { week: '周三', percentage: 88, color: '#41b6ff' },
  { week: '周二', percentage: 86, color: '#41b6ff' },
  { week: '周一', percentage: 85, color: '#41b6ff' },
];

/** 数据统计表 30 行随机数据 + 最新动态前 14 条 */
interface StatRow {
  id: number;
  requiredNumber: number;
  questionNumber: number;
  resolveNumber: number;
  satisfaction: number;
  date: string;
}

function randomBetween(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function formatDate(offsetDays: number): string {
  const d = new Date();
  d.setDate(d.getDate() - offsetDays);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** JS getDay()（0=周日）映射到 DAYS（0=周一）下标 */
function dayLabel(offsetDays: number): string {
  const dayIdx = (new Date(formatDate(offsetDays)).getDay() + 6) % 7;
  return DAYS[dayIdx];
}

const TABLE_DATA: StatRow[] = Array.from({ length: 30 }, (_, index) => ({
  id: index + 1,
  requiredNumber: randomBetween(13500, 19999),
  questionNumber: randomBetween(12600, 16999),
  resolveNumber: randomBetween(13500, 17999),
  satisfaction: randomBetween(95, 100),
  date: formatDate(index),
}));

const LATEST_NEWS = TABLE_DATA.slice(0, 14).map((item, index) => ({
  ...item,
  label: `${formatDate(index)} ${dayLabel(index)}`,
}));

/** 首页：数据卡片 + 分析概览 + 解决概率 + 数据统计 + 最新动态（对齐 Vue welcome） */
export default function WelcomePage(): React.ReactNode {
  const [curWeek, setCurWeek] = useState(0);

  const barData = useMemo(() => {
    const cur = BAR_CHART_DATA[curWeek];
    return DAYS.flatMap((day, i) => [
      { day, type: '需求人数', value: cur.requireData[i] },
      { day, type: '提问数量', value: cur.questionData[i] },
    ]);
  }, [curWeek]);

  const statColumns = [
    { title: '序号', dataIndex: 'id', key: 'id', width: 70 },
    { title: '需求人数', dataIndex: 'requiredNumber', key: 'requiredNumber' },
    { title: '提问数量', dataIndex: 'questionNumber', key: 'questionNumber' },
    { title: '解决数量', dataIndex: 'resolveNumber', key: 'resolveNumber' },
    {
      title: '用户满意度',
      dataIndex: 'satisfaction',
      key: 'satisfaction',
      render: (value: number) => `${value}%`,
    },
    { title: '统计日期', dataIndex: 'date', key: 'date' },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]}>
        {CHART_DATA.map((item) => (
          <Col key={item.name} xs={24} md={12} xxl={6}>
            <Card size="small">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontWeight: 500 }}>{item.name}</span>
                <span
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 6,
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: item.bgColor,
                    color: item.color,
                    fontSize: 16,
                  }}
                >
                  ◆
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <Statistic
                    value={item.value}
                    styles={{
                      content: { fontSize: 22, color: 'rgba(0,0,0,0.88)' },
                    }}
                  />
                  <div style={{ color: '#26ce83', fontWeight: 500 }}>
                    {item.percent}
                  </div>
                </div>
                <div style={{ width: '50%' }}>
                  <Line
                    data={item.data}
                    xField="day"
                    yField="value"
                    height={72}
                    autoFit
                    padding={8}
                    axis={false}
                    legend={false}
                    tooltip={false}
                    style={{ stroke: item.color, lineWidth: 2 }}
                  />
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} xxl={18}>
          <Card
            title="分析概览"
            extra={
              <Segmented
                value={curWeek}
                onChange={(v) => setCurWeek(v as number)}
                options={[
                  { label: '上周', value: 0 },
                  { label: '本周', value: 1 },
                ]}
              />
            }
          >
            <Column
              data={barData}
              xField="day"
              yField="value"
              colorField="type"
              group
              height={320}
              autoFit
              legend={{
                color: {
                  position: 'top',
                },
              }}
            />
          </Card>
        </Col>
        <Col xs={24} xxl={6}>
          <Card title="解决概率">
            {PROGRESS_DATA.map((item, index) => (
              <div
                key={item.week}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginTop: index === 0 ? 8 : 28,
                }}
              >
                <div style={{ flex: 1 }}>
                  <Progress
                    percent={item.percentage}
                    strokeColor={item.color}
                    size={['100%', 20]}
                  />
                </div>
                <span
                  style={{
                    fontSize: 13,
                    color: 'rgba(0,0,0,0.45)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {item.week}
                </span>
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} xxl={18}>
          <Card title="数据统计">
            <Table<StatRow>
              rowKey="id"
              size="small"
              columns={statColumns}
              dataSource={TABLE_DATA}
              pagination={{ pageSize: 10, size: 'small' }}
              scroll={{ y: 440 }}
            />
          </Card>
        </Col>
        <Col xs={24} xxl={6}>
          <Card title="最新动态">
            <div style={{ maxHeight: 480, overflow: 'auto' }}>
              <Timeline
                items={LATEST_NEWS.map((item) => ({
                  content: (
                    <>
                      <div style={{ fontSize: 13, color: 'rgba(0,0,0,0.45)' }}>
                        {item.label}
                      </div>
                      <div style={{ fontSize: 13 }}>
                        {`新增 ${item.requiredNumber} 条问题，${item.resolveNumber} 条已解决`}
                      </div>
                    </>
                  ),
                }))}
              />
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
