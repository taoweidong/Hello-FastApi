/**
 * @name 路由配置
 * @description 静态路由定义；动态菜单由后端 /get-async-routes 下发（app.tsx 中合并）。
 * component 为 src/pages/ 下的相对路径。
 */
export default [
  {
    path: '/user',
    layout: false,
    routes: [
      { path: '/user/login', name: 'login', component: './user/login' },
      { path: '/user', redirect: '/user/login' },
    ],
  },
  { path: '/welcome', name: '首页', icon: 'smile', component: './welcome' },
  // 系统管理
  {
    path: '/system/user',
    name: '用户管理',
    icon: 'user',
    component: './system/user',
  },
  {
    path: '/system/role',
    name: '角色管理',
    icon: 'safety',
    component: './system/role',
  },
  {
    path: '/system/menu',
    name: '菜单管理',
    icon: 'appstore',
    component: './system/menu',
  },
  {
    path: '/system/dept',
    name: '部门管理',
    icon: 'apartment',
    component: './system/dept',
  },
  {
    path: '/system/dictionary',
    name: '字典管理',
    icon: 'book',
    component: './system/dictionary',
  },
  {
    path: '/system/ip-rule',
    name: 'IP规则',
    icon: 'global',
    component: './system/ip-rule',
  },
  {
    path: '/system/config',
    name: '系统配置',
    icon: 'tool',
    component: './system/config',
  },
  {
    path: '/system/notice',
    name: '通知公告',
    icon: 'bell',
    component: './system/notice',
  },
  {
    path: '/system/post',
    name: '岗位管理',
    icon: 'idcard',
    component: './system/post',
  },
  {
    path: '/account-settings',
    name: '个人中心',
    icon: 'userOutlined',
    component: './account/settings',
  },
  // 系统监控
  {
    path: '/monitor/server',
    name: '服务器监控',
    icon: 'monitor',
    component: './monitor/server',
  },
  {
    path: '/monitor/cache',
    name: '缓存监控',
    icon: 'database',
    component: './monitor/cache',
  },
  {
    path: '/monitor/online',
    name: '在线用户',
    icon: 'team',
    component: './monitor/online',
  },
  {
    path: '/monitor/log/login',
    name: '登录日志',
    icon: 'fileText',
    component: './monitor/log/login',
  },
  {
    path: '/monitor/log/operation',
    name: '操作日志',
    icon: 'fileText',
    component: './monitor/log/operation',
  },
  { path: '/', redirect: '/welcome' },
  { path: '*', layout: false, component: './404' },
];
