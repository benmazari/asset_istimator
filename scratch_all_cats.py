import yaml
import psycopg2
import psycopg2.extras

with open(r"c:\Users\benmazari_s\Desktop\amortissement\config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

conn = psycopg2.connect(
    host=cfg["database"]["host"],
    port=cfg["database"]["port"],
    dbname=cfg["database"]["dbname"],
    user=cfg["database"]["user"],
    password=cfg["database"]["password"]
)

with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    cur.execute("""
        SELECT id, name, method_number
        FROM account_asset_category
        ORDER BY id
    """)
    rows = cur.fetchall()
    print("--- ALL CATEGORIES IN ODOO ---")
    for r in rows:
        print(f"ID: {r['id']}, Name: {r['name']}, Method Number (months): {r['method_number']}")

conn.close()
