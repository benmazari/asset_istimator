import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from ui import _load_config
from generator import get_connection

cfg = _load_config()
conn = get_connection(cfg["database"])

with conn.cursor() as cur:
    cur.execute("""
        SELECT aaa.id, aaa.name, aac.id, aac.name, aaa.purchase_date, aaa.date_comptabilisation, aaa.create_date, aaa.state
        FROM account_asset_asset aaa
        JOIN account_asset_category aac ON aac.id = aaa.category_id
        JOIN res_company rc ON rc.id = aaa.company_id
        WHERE rc.name = 'TEKNACHEM ALGERIE'
          AND (EXTRACT(YEAR FROM aaa.date_comptabilisation) = 2025 
               OR EXTRACT(YEAR FROM aaa.purchase_date) = 2025 
               OR EXTRACT(YEAR FROM aaa.create_date) = 2025)
        ORDER BY aac.id, aaa.id
    """)
    rows = cur.fetchall()

conn.close()

print(f"{'Asset ID':<10} | {'Nom Immo':<32} | {'Cat ID':<6} | {'Nom Catégorie':<28} | {'Purchase':<12} | {'Comptabil':<12} | {'Create':<12} | {'State'}")
print("-" * 130)
for r in rows:
    aid, aname, cid, cname, pdate, cdate, crdate, state = r
    print(f"{aid:<10} | {aname[:30]:<32} | {cid:<6} | {cname[:26]:<28} | {str(pdate):<12} | {str(cdate):<12} | {str(crdate)[:10]:<12} | {state}")
