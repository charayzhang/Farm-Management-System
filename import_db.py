"""One-off: import fms-local.sql using connect.py credentials."""
from pathlib import Path
import mysql.connector
import connect

sql_path = Path(__file__).parent / "fms-local.sql"
sql = sql_path.read_text(encoding="utf-8")

conn = mysql.connector.connect(
    user=connect.dbuser,
    password=connect.dbpass,
    host=connect.dbhost,
)
cur = conn.cursor()
for stmt in sql.split(";"):
    s = stmt.strip()
    if s:
        cur.execute(s)
conn.commit()

cur.execute("SHOW TABLES FROM fms")
tables = [row[0] for row in cur.fetchall()]
print("tables:", tables)
for table in ("paddocks", "mobs", "stock", "curr_date"):
    cur.execute(f"SELECT COUNT(*) FROM fms.{table}")
    print(f"{table}:", cur.fetchone()[0])

cur.close()
conn.close()
print("Import OK")
