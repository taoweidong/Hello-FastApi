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
  { path: '/', redirect: '/welcome' },
  { path: '*', layout: false, component: './404' },
];
