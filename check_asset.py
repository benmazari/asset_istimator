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
SELECT 
    aaat.id, 
    aac.name as category_name,
    aaat.date_comptabilisation,
    aaat.purchase_value,
    aaat.state
FROM account_asset_asset aaat
LEFT JOIN account_asset_category aac ON aac.id = aaat.category_id
WHERE aaat.id = 221162
""")

row = cur.fetchone()
if row:
    print(f'ID: {row[0]}')
    print(f'Category: {row[1]}')
    print(f'Date comptabilisation: {row[2]}')
    print(f'Purchase value: {row[3]}')
    print(f'State: {row[4]}')
else:
    print('Asset not found in database.')

conn.close()
