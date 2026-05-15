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

print("--- RUNNING USER'S QUERY ---")
with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    cur.execute("""
        SELECT DISTINCT aaat.id, aac.id as cat_id, aac.name as cat_name, aaat.name as asset_name, aaat.state
        FROM account_asset_asset aaat
        LEFT JOIN account_asset_category aac ON aac.id = aaat.category_id
        WHERE date_part('year', aaat.date_comptabilisation) = '2025'
          AND aaat.company_location_id = 20
    """)
    user_rows = cur.fetchall()
    print(f"User query returned {len(user_rows)} assets.")
    for r in user_rows:
        print(f"ID: {r['id']}, CatID: {r['cat_id']}, Cat: {r['cat_name']}, Asset: {r['asset_name']}, State: {r['state']}")

print("\n--- RUNNING BACKEND QUERY (TEKNACHEM ALGERIE) ---")
with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    cur.execute("""
        SELECT DISTINCT aaat.id, aac.id as cat_id, aac.name as cat_name, aaat.name as asset_name, aaat.state,
                        societe_comptable.name as comp_name, aaat.company_location_id, aaat.company_id
        FROM account_asset_asset aaat
        JOIN account_asset_category aac ON aac.id = aaat.category_id
        LEFT JOIN res_company societe_comptable ON societe_comptable.id = aaat.company_id
        WHERE EXTRACT(YEAR FROM aaat.date_comptabilisation) = 2025
          AND COALESCE(societe_comptable.name, 'Non défini') = 'TEKNACHEM ALGERIE'
    """)
    backend_rows = cur.fetchall()
    print(f"Backend query returned {len(backend_rows)} assets.")
    for r in backend_rows:
        print(f"ID: {r['id']}, CatID: {r['cat_id']}, Cat: {r['cat_name']}, Asset: {r['asset_name']}, State: {r['state']}, LocID: {r['company_location_id']}, CompID: {r['company_id']}")

conn.close()
