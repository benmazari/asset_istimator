import sys
sys.path.insert(0, 'C:/Users/benmazari_s/Desktop/amortissement')
import yaml, psycopg2, time

with open('C:/Users/benmazari_s/Desktop/amortissement/config.yaml', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

db = cfg['database']
conn = psycopg2.connect(
    host=db['host'], port=db['port'], dbname=db['dbname'],
    user=db['user'], password=db['password'], connect_timeout=10
)
cur = conn.cursor()

print('Counting lines...')
cur.execute("SELECT COUNT(*) FROM account_asset_depreciation_line")
print('Total lines in table:', cur.fetchone()[0])

print('Explaining lines query...')
t0 = time.time()
cur.execute("EXPLAIN ANALYZE SELECT * FROM account_asset_depreciation_line WHERE asset_id = ANY(ARRAY[34473, 34474, 34475])")
for r in cur.fetchall():
    print(r[0])
print(f'Time: {time.time() - t0:.2f}s')

conn.close()
