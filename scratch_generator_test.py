import os
import yaml
import psycopg2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
cfg_path = os.path.join(SCRIPT_DIR, "config.yaml")
with open(cfg_path, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

db = cfg["database"]
conn = psycopg2.connect(
    dbname=db["dbname"],
    user=db["user"],
    password=db["password"],
    host=db["host"],
    port=db["port"]
)

with conn.cursor() as cur:
    cur.execute("""
        SELECT aaat.id AS id_immo,
               aaat.purchase_value,
               aaat.date_comptabilisation AS start_date,
               aac.id AS cat_id,
               aac.name AS category
        FROM account_asset_asset aaat
        JOIN account_asset_category aac ON aac.id = aaat.category_id
        JOIN res_company societe_comptable ON societe_comptable.id = aaat.company_id
        WHERE societe_comptable.name = 'TEKNACHEM ALGERIE'
          AND EXTRACT(YEAR FROM aaat.date_comptabilisation) = 2025
    """)
    assets = cur.fetchall()

print(f"TOTAL: {len(assets)}")
for a in assets:
    print(f"ID: {a[0]}, PV: {a[1]}, Start: {a[2]}, Cat: {a[4]}")
