import sys
sys.path.insert(0, 'C:/Users/benmazari_s/Desktop/amortissement')
import yaml, psycopg2

with open('C:/Users/benmazari_s/Desktop/amortissement/config.yaml', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

db = cfg['database']
conn = psycopg2.connect(
    host=db['host'], port=db['port'], dbname=db['dbname'],
    user=db['user'], password=db['password'], connect_timeout=10
)
cur = conn.cursor()

cur.execute("""
    SELECT asset_id, depreciation_date, COUNT(*)
    FROM account_asset_depreciation_line
    WHERE asset_id IN (
        SELECT aaat.id FROM account_asset_asset aaat 
        JOIN account_asset_category aac ON aac.id = aaat.category_id 
        WHERE aac.name ILIKE 'B_timents%'
    )
    GROUP BY asset_id, depreciation_date
    HAVING COUNT(*) > 1
""")
dups = cur.fetchall()
print(f'Duplicate dates found for {len(dups)} asset-month combinations.')
if dups:
    print('Example duplicates:', dups[:5])

cur.execute("""
    SELECT COUNT(*)
    FROM account_asset_depreciation_line
    WHERE asset_id IN (
        SELECT aaat.id FROM account_asset_asset aaat 
        JOIN account_asset_category aac ON aac.id = aaat.category_id 
        WHERE aac.name ILIKE 'B_timents%'
    )
""")
print(f'Total real lines for these assets: {cur.fetchone()[0]}')

conn.close()
