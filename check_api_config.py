import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from ui import _load_config
from generator import get_connection

cfg = _load_config()
db = cfg["database"]
cats = cfg.get("categories", [])

conn = get_connection(db)
all_cids = []
for c in cats:
    all_cids.extend(c.get("ids", []))

with conn.cursor() as cur:
    cur.execute("""
        SELECT id, method_number
        FROM account_asset_category
        WHERE id = ANY(%s)
    """, [all_cids])
    m_map = {r[0]: r[1] for r in cur.fetchall()}

conn.close()

for c in cats:
    cids = c.get("ids", [])
    if cids and cids[0] in m_map and m_map[cids[0]]:
        c["old_years"] = round(float(m_map[cids[0]]) / 12.0, 2)
    else:
        c["old_years"] = c.get("years", 10.0)

print(f"{'Cat ID':<8} | {'Label':<30} | {'old_years (Odoo)':<18} | {'years (Excel)':<15} | {'Modified?'}")
print("-" * 85)
for c in cats:
    cid = c["ids"][0]
    oy = c.get("old_years")
    y = c.get("years")
    mod = "YES" if oy != y else "NO"
    print(f"{cid:<8} | {c['label']:<30} | {str(oy):<18} | {str(y):<15} | {mod}")
