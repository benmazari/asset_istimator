import yaml
import psycopg2
import psycopg2.extras

with open(r"c:\Users\benmazari_s\Desktop\amortissement\config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

configured_ids = set()
for cat in cfg.get("categories", []):
    configured_ids.update(cat.get("ids", []))

conn = psycopg2.connect(
    host=cfg["database"]["host"],
    port=cfg["database"]["port"],
    dbname=cfg["database"]["dbname"],
    user=cfg["database"]["user"],
    password=cfg["database"]["password"]
)

with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    cur.execute("""
        SELECT DISTINCT aaat.id, aac.id as cat_id, aac.name as cat_name, aaat.name as asset_name, aaat.state
        FROM account_asset_asset aaat
        LEFT JOIN account_asset_category aac ON aac.id = aaat.category_id
        WHERE date_part('year', aaat.date_comptabilisation) = '2025'
          AND aaat.company_location_id = 20
        ORDER BY aac.id
    """)
    rows = cur.fetchall()

print("| Asset ID | Category ID | Category Name | Asset Name | Status | Configured? |")
print("|---|---|---|---|---|---|")
for r in rows:
    is_conf = "YES" if r['cat_id'] in configured_ids else "NO (Excluded)"
    # Safe encoding for print
    cat_name = r['cat_name'].encode('ascii', 'ignore').decode('ascii')
    asset_name = r['asset_name'].encode('ascii', 'ignore').decode('ascii')
    print(f"| {r['id']} | {r['cat_id']} | {cat_name} | {asset_name} | {r['state']} | {is_conf} |")

conn.close()
