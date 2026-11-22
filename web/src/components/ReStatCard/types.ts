import type { PropType } from "vue";

/** 趋势标签：up 上升 / down 下降 / flat 持平 */
export type StatTrend = {
  text: string;
  type: "up" | "down" | "flat";
};

export const statCardProps = {
  /** 统计项名称（左上角，与图标同行） */
  title: {
    type: String,
    required: true
  },
  /** 图标名（IconifyIconOffline 离线图标，须在 offlineIconNames 白名单内，如 "ri/admin-line"） */
  icon: {
    type: String,
    required: true
  },
  /** 数值（内部用 ReNormalCountTo 做数字动画，startVal 固定从 0 起） */
  value: {
    type: Number,
    default: 0
  },
  /** 数值单位后缀，如 "人"、"次" */
  suffix: {
    type: String,
    default: ""
  },
  /** 可选副文案（数值下方灰色小字） */
  subText: {
    type: String,
    default: ""
  },
  /** 可选趋势标签（右上角小徽标） */
  trend: {
    type: Object as PropType<StatTrend>,
    default: undefined
  },
  /** 图标颜色，默认 EP 主题色（传 CSS 变量或色值均可） */
  iconColor: {
    type: String,
    default: ""
  },
  /** 图标块背景色，默认 EP 主题色淡色底（深色模式自动随 EP 变量切换） */
  iconBg: {
    type: String,
    default: ""
  },
  /** 数字动画时长（ms），透传 ReNormalCountTo */
  duration: {
    type: Number,
    default: 1300
  }
};
