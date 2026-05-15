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

# Show all category names and their asset count
cur.execute("""
    SELECT aac.name, COUNT(aaat.id) as nb
    FROM account_asset_category aac
    LEFT JOIN account_asset_asset aaat
        ON aaat.category_id = aac.id
        AND aaat.state NOT IN ('close', 'draft')
    GROUP BY aac.name
    ORDER BY nb DESC
""")
rows = cur.fetchall()
print(f"{'Category':<50} {'Assets':>8}")
print("-" * 60)
for name, nb in rows:
    print(f"{name:<50} {nb:>8}")

conn.close()
