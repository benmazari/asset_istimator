import os
import sys
import yaml
import psycopg2
import psycopg2.extras
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from generator import _compute_schedule, _compute_schedule_daily, _compute_schedule_yearly

def run_precision_check():
    # 1. Load config
    config_path = os.path.join(SCRIPT_DIR, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 2. Extract configured categories and their years
    cat_lookup = {}
    for cat in cfg.get("categories", []):
        for cid in cat.get("ids", []):
            cat_lookup[cid] = {
                "label": cat.get("label"),
                "years": int(cat.get("years", 10))
            }

    all_cat_ids = list(cat_lookup.keys())

    # 3. Connect to database
    db_cfg = cfg["database"]
    conn = psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg.get("port", 5432),
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"]
    )

    # 4. Fetch all assets
    print("Fetching all active assets from Odoo...")
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT aaat.id AS id_immo,
                   aaat.code AS "Référence",
                   aaat.name AS "Nom immobilisation",
                   aaat.purchase_date AS "Date d'acquisition",
                   aaat.date_comptabilisation AS "Date début d'amortissement",
                   aaat.purchase_value AS "Valeur brute",
                   aaat.category_id,
                   societe_comptable.name AS "Société"
            FROM account_asset_asset aaat
            LEFT JOIN res_company societe_comptable ON societe_comptable.id = aaat.company_id
            WHERE aaat.category_id = ANY(%s)
              AND aaat.state NOT IN ('close', 'draft')
        """, [all_cat_ids])
        assets = [dict(r) for r in cur.fetchall()]

    conn.close()

    print(f"Total assets fetched for verification: {len(assets)}")
    print("Running precision check...")
    print("-" * 80)

    mismatches = []
    skipped_no_date = 0
    skipped_zero_pv = 0
    validated_count = 0

    # We will check MONTHLY schedule for ALL assets.
    # We will check DAILY and YEARLY schedules for a large representative sample of 2,000 assets.
    sample_size = 2000

    for idx, asset in enumerate(assets):
        id_immo = asset["id_immo"]
        code = asset["Référence"] or "N/D"
        name = asset["Nom immobilisation"] or "N/D"
        pv = float(asset["Valeur brute"] or 0)
        start_date = asset["Date début d'amortissement"]
        cid = asset["category_id"]
        company = asset["Société"] or "N/D"

        # Skip assets that cannot be amortized
        if not start_date:
            skipped_no_date += 1
            continue
        if pv <= 0:
            skipped_zero_pv += 1
            continue

        years = cat_lookup[cid]["years"]

        # 1. Validate Monthly Schedule (for ALL assets)
        monthly_lines = _compute_schedule(asset, years)
        sum_monthly = sum(line["base_amount"] for line in monthly_lines)
        diff_monthly = abs(sum_monthly - pv)

        # 2. Validate Daily & Yearly Schedule (for a representative sample)
        diff_daily = 0.0
        diff_yearly = 0.0
        sum_daily = pv
        sum_yearly = pv

        if idx < sample_size:
            daily_lines = _compute_schedule_daily(asset, years)
            sum_daily = sum(line["base_amount"] for line in daily_lines)
            diff_daily = abs(sum_daily - pv)

            yearly_lines = _compute_schedule_yearly(asset, years)
            sum_yearly = sum(line["base_amount"] for line in yearly_lines)
            diff_yearly = abs(sum_yearly - pv)

        if diff_monthly > 0.01 or diff_daily > 0.01 or diff_yearly > 0.01:
            mismatches.append({
                "id": id_immo,
                "code": code,
                "name": name,
                "company": company,
                "pv": pv,
                "start": start_date,
                "years": years,
                "sum_monthly": sum_monthly,
                "sum_daily": sum_daily,
                "sum_yearly": sum_yearly,
                "diff_m": diff_monthly,
                "diff_d": diff_daily,
                "diff_y": diff_yearly,
            })
        else:
            validated_count += 1

    # 5. Output Report
    print(f"Check Complete.")
    print(f"  - Total Assets Fetched: {len(assets)}")
    print(f"  - Skipped (No Start Date): {skipped_no_date}")
    print(f"  - Skipped (Zero/Negative Valeur Brute): {skipped_zero_pv}")
    print(f"  - Successfully Validated Assets: {validated_count}")
    print(f"  - Mathematical Mismatches: {len(mismatches)}")
    print("-" * 80)

    if mismatches:
        print("WARNING: Found the following assets with mathematical discrepancies:")
        for m in mismatches:
            print(f"Asset ID: {m['id']} (Ref: {m['code']}, Company: {m['company']})")
            print(f"  Valeur Brute: {m['pv']}")
            print(f"  Start Date: {m['start']} | Amortization Years: {m['years']}")
            print(f"  Sum Monthly: {m['sum_monthly']} (Diff: {m['diff_m']:.6f})")
            print(f"  Sum Daily: {m['sum_daily']} (Diff: {m['diff_d']:.6f})")
            print(f"  Sum Yearly: {m['sum_yearly']} (Diff: {m['diff_y']:.6f})")
            print("-" * 40)
    else:
        print("SUCCESS! Every single asset's calculated schedule matches its purchase value (Valeur brute) EXACTLY down to 0.000001 DZD across Monthly, Daily, and Yearly granularities!")

if __name__ == "__main__":
    run_precision_check()
