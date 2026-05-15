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
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE date_comptabilisation IS NULL) as null_date,
        COUNT(*) FILTER (WHERE purchase_value = 0 OR purchase_value IS NULL) as zero_value
    FROM account_asset_asset aaat 
    JOIN account_asset_category aac ON aac.id = aaat.category_id 
    WHERE aac.name ILIKE 'B_timents%'
""")
print('total, null_date, zero_value:', cur.fetchone())

conn.close()
