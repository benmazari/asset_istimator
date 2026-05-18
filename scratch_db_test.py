import requests
import json

# Get cat_ids by querying /api/config
r_cfg = requests.get("http://localhost:5000/api/config")
categories = r_cfg.json().get("categories", [])
modified_cat_ids = []
for cat in categories:
    is_modified = cat.get("old_years") is not None and cat.get("old_years") != cat.get("years") and not cat.get("is_virtual")
    if is_modified:
        modified_cat_ids.extend(cat["ids"])

print(f"Modified Category IDs: {modified_cat_ids}")

url = "http://localhost:5000/api/dashboard"
params = {
    "societe": "TEKNACHEM ALGERIE",
    "date": "31/12/2025",
    "gran": "monthly",
    "non_amortie": "true",
    "year_debut": "2025",
    "year_debut_type": "start_date",
    "cat_ids": ",".join(map(str, modified_cat_ids))
}

r = requests.get(url, params=params)
data = r.json()

print("\n=== GAP BY COMPANY (WITH CAT IDS) ===")
for comp in data.get("gap_by_company", []):
    if comp["company"] == "TEKNACHEM ALGERIE":
        print(json.dumps(comp, indent=2))

print("\n=== ECONOMY DETAILS (WITH CAT IDS) ===")
total_count = 0
total_pv = 0
total_real = 0
total_est = 0
total_gap = 0
for econ in data.get("economy_details", []):
    if econ["company"] == "TEKNACHEM ALGERIE":
        total_count += econ["count"]
        total_pv += econ["total_pv"]
        total_real += econ["real"]
        total_est += econ["estimated"]
        total_gap += econ["gap"]
        print(f"Category: {econ['category']}, Count: {econ['count']}, PV: {econ['total_pv']:.2f}, Real: {econ['real']:.2f}, Est: {econ['estimated']:.2f}, Gap: {econ['gap']:.2f}")

print(f"\nSum of Economy Details: Count={total_count}, PV={total_pv:.2f}, Real={total_real:.2f}, Est={total_est:.2f}, Gap={total_gap:.2f}")

print("\n=== KPIS ===")
print(json.dumps(data.get("kpis", {}), indent=2))
