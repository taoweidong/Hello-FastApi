"""缓存 TTL 计算助手。

黑名单与在线会话分属不同存储组件，但都必须按 ``expires_at`` 计算剩余秒数，
故把算法收敛到这一处，避免两侧对"过期"的判定漂移。
"""

import math
from datetime import datetime, timezone


def remaining_seconds(expires_at: datetime) -> int:
    """计算过期时间距当前时间的剩余秒数。

    用 ``ceil`` 而非 ``int``：调用方常以「now + 配置秒数」得到 ``expires_at``，
    两次 ``datetime.now()`` 之间只要有微小间隔，``int`` 就会把 86400 截断成 86399，
    使实际 TTL 比配置值少 1 秒。向上取整保证条目至少存活到预期时刻
    （已过期的仍被 ``max(..., 0)`` 收敛为 0，由调用方按「无需处理」分支拦截）。
    """
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = (expires_at - now).total_seconds()
    return max(math.ceil(delta), 0)
