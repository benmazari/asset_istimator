import os
import sys
import yaml
import psycopg2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from ui import _load_config
from generator import get_connection

cfg = _load_config()
conn = get_connection(cfg["database"])

# Load config mappings
yaml_cats = {}
for c in cfg.get("categories", []):
    for cid in c["ids"]:
        yaml_cats[cid] = {
            "label": c.get("label", "?"),
            "years": c.get("years", 10),
        }

with conn.cursor() as cur:
    cur.execute("""
        SELECT aac.id, aac.name, aac.method_number, COUNT(aaa.id) as asset_count
        FROM account_asset_category aac
        LEFT JOIN account_asset_asset aaa ON aaa.category_id = aac.id
        GROUP BY aac.id, aac.name, aac.method_number
        ORDER BY aac.id
    """)
    rows = cur.fetchall()

conn.close()

print(f"{'ID':<5} | {'Nom Catégorie (Odoo)':<38} | {'Actifs':<7} | {'Durée Odoo (Ans)':<18} | {'Durée Excel (Ans)':<18} | {'Statut'}")
print("-" * 115)

for r in rows:
    cid, name, method_number, count = r
    odoo_years = round((method_number or 0) / 12.0, 2)
    
    yc = yaml_cats.get(cid)
    if yc:
        excel_years = yc["years"]
        status = "Modifiée" if odoo_years != excel_years else "Identique"
    else:
        excel_years = "Non configuré"
        status = "Inactif/Omis"
        
    print(f"{cid:<5} | {name:<38} | {count:<7} | {odoo_years:<18} | {str(excel_years):<18} | {status}")
