from data_cache import DataCache
import yaml

with open('config.yaml') as f:
    cfg = yaml.safe_load(f)

cache = DataCache()
cache.refresh(cfg['database'])
for s in sorted(cache.societes):
    print(f"'{s}'")
