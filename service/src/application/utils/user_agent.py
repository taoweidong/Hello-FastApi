"""User-Agent 解析工具。

从 User-Agent 字符串中粗略提取浏览器与操作系统信息，
供审计日志中间件与登录日志记录等场景复用。
"""


def extract_user_agent_info(user_agent: str) -> tuple[str, str]:
    """从 User-Agent 字符串中粗略提取浏览器和操作系统信息。

    Args:
        user_agent: User-Agent 请求头原文（可为空字符串）

    Returns:
        (browser, system) 元组，无法识别时返回 "unknown"
    """
    browser = "unknown"
    system = "unknown"

    if not user_agent:
        return browser, system

    ua_lower = user_agent.lower()
    if "windows" in ua_lower:
        system = "Windows"
    elif "mac os" in ua_lower:
        system = "Mac OS"
    elif "linux" in ua_lower:
        system = "Linux"
    elif "android" in ua_lower:
        system = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        system = "iOS"

    if "edg/" in ua_lower:
        browser = "Edge"
    elif "chrome/" in ua_lower:
        browser = "Chrome"
    elif "firefox/" in ua_lower:
        browser = "Firefox"
    elif "safari/" in ua_lower and "chrome/" not in ua_lower:
        browser = "Safari"

    return browser, system
