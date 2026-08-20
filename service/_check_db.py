"""临时脚本：检查 dev.db 表结构与用户。用完即删。"""

import sqlite3

conn = sqlite3.connect("sql/dev.db")
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", tables)
for t in tables:
    if "user" in t.lower():
        try:
            rows = conn.execute(f"SELECT username FROM {t} LIMIT 10").fetchall()
            print(t, "->", rows)
        except Exception as exc:
            print(t, "error:", exc)
conn.close()
