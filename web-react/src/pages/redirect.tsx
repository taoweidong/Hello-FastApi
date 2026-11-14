import { history, useSearchParams } from '@umijs/max';
import { useEffect } from 'react';

/**
 * /redirect 兼容页（对齐 Vue src/layout/redirect.vue）：
 * 菜单刷新等场景通过 /redirect/<path> 跳转，本页解析路径参数后立即
 * replace 到目标路由并透传其余 query；也支持 ?redirect=/xxx 形式。
 */
export default function RedirectPage(): null {
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // 1) query.redirect 优先（如 ?redirect=/system/user）
    const redirectQuery = searchParams.get('redirect');
    if (redirectQuery) {
      history.replace(redirectQuery);
      return;
    }
    // 2) 路径参数：/redirect/system/user → /system/user（保留其余 query）
    const rest = searchParams.toString();
    const current = window.location.pathname;
    const pathParam = current.replace(/^\/redirect\/?/, '');
    const target = pathParam ? `/${pathParam}` : '/';
    history.replace(rest ? `${target}?${rest}` : target);
  }, [searchParams]);

  return null;
}
