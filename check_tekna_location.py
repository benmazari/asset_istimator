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
        SELECT aaa.id, aaa.name, aac.id, aac.name, aaa.company_id, rc1.name, aaa.company_location_id, rc2.name, aaa.date_comptabilisation
        FROM account_asset_asset aaa
        JOIN account_asset_category aac ON aac.id = aaa.category_id
        LEFT JOIN res_company rc1 ON rc1.id = aaa.company_id
        LEFT JOIN res_company rc2 ON rc2.id = aaa.company_location_id
        WHERE (aaa.company_location_id = 20 OR rc1.name = 'TEKNACHEM ALGERIE')
          AND EXTRACT(YEAR FROM aaa.date_comptabilisation) = 2025
        ORDER BY aac.id, aaa.id
    """)
    rows = cur.fetchall()

conn.close()

print(f"{'Asset ID':<10} | {'Nom Immo':<30} | {'Cat ID':<6} | {'Nom Catégorie':<28} | {'Comp ID (rc1)':<22} | {'Loc ID (rc2)':<22} | {'Date Comptab'}")
print("-" * 140)
for r in rows:
    aid, aname, cid, cname, comp_id, comp_name, loc_id, loc_name, cdate = r
    cn = comp_name[:14] if comp_name else 'NULL'
    ln = loc_name[:14] if loc_name else 'NULL'
    print(f"{aid:<10} | {aname[:28]:<30} | {cid:<6} | {cname[:26]:<28} | {f'{comp_id} ({cn})':<22} | {f'{loc_id} ({ln})':<22} | {str(cdate)}")
