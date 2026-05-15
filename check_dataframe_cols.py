import os
import sys
import yaml
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from generator import _compute_schedule

# Mock a simple asset row
asset_row = {
    "id_immo": 258743,
    "Référence": "REF001",
    "Nom immobilisation": "TEST ASSET",
    "Date d'acquisition": None,
    "Date début d'amortissement": date(2025, 1, 1),
    "Valeur brute": 120000.0,
    "category_id": 18,
    "Durée d'amortissement (Odoo)": 3.0, # from SQL Round
}

print("Running test monthly calculation for sample asset...")
schedule = _compute_schedule(asset_row, years=10)

# Build a mock row just like generator.py does
d = schedule[0]["dep_date"]
row = {
    **asset_row,
    "Durée d'amortissement (Excel)": 10,
    "Date de dépréciation": d,
    "Amortissement courant estimé": schedule[0]["base_amount"],
    "Montant déjà amorti estimé": schedule[0]["cum_estimated"],
    "Période suivante estimée": schedule[0]["remaining_estimated"],
}

print("\nResulting columns in generated row:")
for k, v in row.items():
    print(f"  - {k}: {v}")
