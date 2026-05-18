import threading
import time
from datetime import datetime
from db import get_connection

class DataCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_update = None
        self.assets = []
        self.lines = {} # asset_id -> list of (date_str, amount, depreciated_value)
        self.dates = []
        self.societes = []
        self.is_loading = False
        self.error = None

    def refresh(self, cfg):
        if self.is_loading:
            return
        
        self.is_loading = True
        self.error = None
        conn = None
        
        try:
            conn = get_connection(cfg["database"])
            
            # Virtual overrides mapping
            v_map = {
                245131: -1, 245132: -1, 245133: -1,
                246689: -2, 247684: -2, 247904: -2
            }
            
            # 1. Fetch Assets (standard tuple cursor)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT aaat.id, 
                           aaat.code, 
                           aaat.name,
                           aaat.purchase_date, 
                           aaat.date_comptabilisation,
                           aaat.purchase_value, 
                           aaat.method_number,
                           aaat.method_period,
                           aac.id AS cat_id,
                           COALESCE(societe_comptable.name, 'Non défini'),
                           aaat.state
                    FROM account_asset_asset aaat
                    JOIN account_asset_category aac ON aac.id = aaat.category_id
                    LEFT JOIN res_company societe_comptable ON societe_comptable.id = aaat.company_id
                """)
                assets_raw = cur.fetchall()
                
            assets = []
            societes_set = set()
            for r in assets_raw:
                aid = r[0]
                cid = v_map.get(aid, r[8])
                comp = r[9]
                if comp != 'Non défini':
                    societes_set.add(comp)
                assets.append({
                    "id_immo": aid,
                    "code": r[1],
                    "asset_name": r[2],
                    "purchase_date": r[3],
                    "start_date": r[4],
                    "purchase_value": float(r[5] or 0),
                    "method_number": r[6],
                    "method_period": r[7],
                    "cat_id": cid,
                    "company_name": comp,
                    "state": r[10]
                })
                
            # 2. Fetch Lines (standard tuple cursor)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT asset_id, depreciation_date, amount, depreciated_value
                    FROM account_asset_depreciation_line
                    WHERE depreciation_date IS NOT NULL
                """)
                lines_raw = cur.fetchall()
                
            lines_dict = {}
            dates_set = set()
            for r in lines_raw:
                aid = r[0]
                if aid not in lines_dict:
                    lines_dict[aid] = []
                
                d_date = r[1]
                d_str = d_date.strftime("%Y-%m-%d") if d_date else None
                if d_str:
                    dates_set.add(d_str)
                amt = float(r[2] or 0)
                dep_val = float(r[3] or 0)
                
                lines_dict[aid].append((d_str, amt, dep_val))
                
            sorted_dates = sorted(list(dates_set), reverse=True)
            sorted_societes = sorted(list(societes_set))
            
            with self.lock:
                self.assets = assets
                self.lines = lines_dict
                self.dates = sorted_dates
                self.societes = sorted_societes
                self.last_update = datetime.now()
                
        except Exception as e:
            self.error = str(e)
            print(f"[CACHE ERROR] {self.error}")
        finally:
            self.is_loading = False
            if conn:
                try:
                    conn.close()
                except:
                    pass

# Global Singleton
global_cache = DataCache()

# Worker and thread starter removed. Manual refresh is handled via api_refresh_cache in ui.py.
