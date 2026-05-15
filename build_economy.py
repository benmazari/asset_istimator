import re

with open('templates/economy.html', 'r', encoding='utf-8') as f:
    content = f.read()

script_match = re.search(r'(<script>\s*feather\.replace\(\);.*?</script>)', content, re.DOTALL)
if not script_match:
    # fallback to function fmt
    script_match = re.search(r'(<script>\s*function fmt.*?</script>)', content, re.DOTALL)
if not script_match:
    raise Exception('Main application script tag not found')
script_content = script_match.group(1)

new_html = f"""<!DOCTYPE html>
<html lang="fr" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Amortissement — Analyse d'Économie</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <script src="https://unpkg.com/feather-icons"></script>

  <style>
    :root {{
      --bg: #f5f6fa;
      --surface: #ffffff;
      --surface2: #f8fafc;
      --border: #e2e8f0;
      --accent: #4f46e5;
      --accent-hover: #4338ca;
      --accent-light: #e0e7ff;
      --text: #1e293b;
      --text-muted: #64748b;
      --ok: #22c55e;
      --err: #ef4444;
      --warn: #f59e0b;
      --radius: 16px;
      --shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    }}

    [data-theme="dark"] {{
      --bg: #0f1117;
      --surface: #1a1d27;
      --surface2: #22263a;
      --border: #2e3350;
      --accent: #4f7df3;
      --accent-hover: #3b66d5;
      --accent-light: rgba(79,125,243,0.15);
      --text: #e2e8f0;
      --text-muted: #8892aa;
      --shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      height: 100vh;
      overflow: hidden;
      display: flex;
      transition: background 0.3s ease, color 0.3s ease;
    }}

    /* ── Sidebar ── */
    .sidebar {{
      width: 260px;
      background: var(--surface);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      padding: 24px;
      transition: background 0.3s ease, border 0.3s ease;
      z-index: 10;
    }}
    .logo {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 40px;
    }}
    .logo-icon {{
      width: 36px; height: 36px;
      background: var(--accent);
      color: white;
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; font-weight: bold;
    }}
    .logo h1 {{ font-size: 20px; font-weight: 700; color: var(--text); }}
    
    .sidebar-nav {{
      display: flex; flex-direction: column; gap: 8px; flex: 1;
    }}
    .sidebar-nav a {{
      display: flex; align-items: center; gap: 12px;
      padding: 12px 16px;
      text-decoration: none;
      color: var(--text-muted);
      font-weight: 500; font-size: 14px;
      border-radius: 12px;
      transition: all 0.2s;
    }}
    .sidebar-nav a i {{ font-size: 18px; font-style: normal; width: 24px; text-align: center; }}
    .sidebar-nav a:hover {{ background: var(--surface2); color: var(--text); }}
    .sidebar-nav a.active {{ background: var(--accent); color: white; box-shadow: 0 4px 12px var(--accent-light); }}
    .sidebar-nav a.active i {{ color: white; }}

    .sidebar-cta {{
      background: var(--accent);
      border-radius: 16px;
      padding: 20px;
      color: white;
      text-align: center;
      box-shadow: 0 8px 20px var(--accent-light);
    }}
    .sidebar-cta h3 {{ font-size: 14px; font-weight: 600; margin-bottom: 6px; }}
    .sidebar-cta p {{ font-size: 11px; opacity: 0.8; margin-bottom: 12px; line-height: 1.4; }}
    .btn-theme {{
      background: white; color: var(--accent);
      border: none; border-radius: 20px;
      padding: 8px 16px; font-size: 12px; font-weight: 600;
      cursor: pointer; width: 100%; transition: transform 0.2s;
    }}
    [data-theme="dark"] .btn-theme {{ background: #1e293b; color: white; }}
    .btn-theme:hover {{ transform: translateY(-2px); }}

    /* ── Main Content ── */
    .main-wrapper {{
      flex: 1;
      display: flex; flex-direction: column;
      overflow: hidden;
    }}

    /* ── Topbar ── */
    .topbar {{
      height: 80px;
      padding: 0 32px;
      display: flex; align-items: center; justify-content: space-between;
      background: var(--bg);
      flex-shrink: 0;
    }}
    .page-title {{ font-size: 24px; font-weight: 700; color: var(--text); }}
    .topbar-right {{ display: flex; align-items: center; gap: 20px; }}
    .search-bar {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 10px 20px;
      display: flex; align-items: center; gap: 8px;
      width: 260px;
      box-shadow: var(--shadow);
    }}
    .search-bar input {{
      border: none; background: transparent; outline: none;
      color: var(--text); font-size: 13px; width: 100%;
    }}
    .search-bar input::placeholder {{ color: var(--text-muted); }}
    .profile {{
      display: flex; align-items: center; gap: 10px;
    }}
    .profile-img {{
      width: 40px; height: 40px; border-radius: 50%;
      background: var(--surface2); border: 1px solid var(--border);
      display: flex; align-items: center; justify-content: center; font-size: 18px;
    }}
    .profile-info {{ display: flex; flex-direction: column; }}
    .profile-name {{ font-size: 13px; font-weight: 600; }}
    .profile-role {{ font-size: 11px; color: var(--text-muted); }}

    /* ── Content ── */
    .content-area {{
      flex: 1; overflow-y: auto;
      padding: 0 32px 32px;
      display: flex; flex-direction: column; gap: 24px;
    }}
    
    /* ── Cards ── */
    .card {{
      background: var(--surface);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
      padding: 24px;
    }}
    .card-title {{
      font-size: 15px; font-weight: 600; color: var(--text);
      margin-bottom: 20px;
    }}

    /* ── Filters Bar ── */
    .filters-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }}
    .field {{ display: flex; flex-direction: column; gap: 6px; }}
    label {{ font-size: 12px; font-weight: 600; color: var(--text-muted); }}
    select, input[type=text], input[type=number] {{
      width: 100%;
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; color: var(--text);
      font-family: 'Inter', sans-serif; font-size: 13px;
      padding: 10px 14px; outline: none; transition: all .2s;
    }}
    select:focus, input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }}
    
    .cat-tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; max-height: 120px; overflow-y: auto; padding-right: 5px; }}
    .cat-tags::-webkit-scrollbar {{ width: 6px; }}
    .cat-tags::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

    .cat-tag {{
      padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border);
      background: var(--surface2); color: var(--text-muted); font-size: 12px; font-weight: 500;
      cursor: pointer; transition: all .2s ease;
    }}
    .cat-tag:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
    .cat-tag.sel {{ background: var(--accent-light); border-color: var(--accent); color: var(--accent); font-weight: 600; }}
    
    .btn-apply {{
      width: 100%; height: 44px; border-radius: 12px;
      font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600;
      cursor: pointer; border: none; background: var(--accent); color: #fff;
      box-shadow: 0 4px 16px var(--accent-light); transition: all .2s;
    }}
    .btn-apply:hover {{ background: var(--accent-hover); transform: translateY(-2px); }}

    /* ── Table ── */
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{
      font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;
      padding: 12px 16px; text-align: left; border-bottom: 2px solid var(--border);
      background: var(--surface2);
    }}
    th:first-child {{ border-top-left-radius: 10px; }}
    th:last-child {{ border-top-right-radius: 10px; }}
    td {{ padding: 12px 16px; border-bottom: 1px solid var(--border); color: var(--text); }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: var(--surface2); }}
    
    .tag-pos {{ background: rgba(34, 197, 94, 0.1); color: #16a34a; padding: 4px 8px; border-radius: 6px; font-weight: 600; display: inline-block; }}
    .tag-neg {{ background: rgba(239, 68, 68, 0.1); color: #dc2626; padding: 4px 8px; border-radius: 6px; font-weight: 600; display: inline-block; }}
    .tag-zero {{ color: var(--text-muted); }}
    
    .yr-old {{ color: var(--warn); font-weight: 600; }}
    .yr-new {{ color: var(--accent); font-weight: 600; }}
    
    tr.child-row td:nth-child(2) {{ padding-left: 32px; color: var(--text-muted); }}
    tr.asset-row td:nth-child(2) {{ padding-left: 56px; color: var(--text-muted); font-size: 12px; }}
    tr.asset-row:hover td {{ background: var(--accent-light); }}

    /* ── Total Saving Block ── */
    .total-block {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 24px;
      display: flex; align-items: center; justify-content: space-between;
      box-shadow: var(--shadow);
    }}

    /* ── Loading ── */
    .loading {{
      display: none; position: fixed; inset: 0; background: rgba(255,255,255,0.7);
      backdrop-filter: blur(4px); z-index: 100; align-items: center; justify-content: center; flex-direction: column; gap: 14px;
    }}
    [data-theme="dark"] .loading {{ background: rgba(15,17,23,0.7); }}
    .loading.show {{ display: flex; }}
    .spinner {{ width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }}

    /* Export button */
    .btn-export {{
      padding: 10px 16px; background: #22c55e; color: #fff; border: none; border-radius: 10px;
      font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; display:flex; align-items:center; gap:6px;
      box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2);
    }}
    .btn-export:hover {{ background: #16a34a; transform: translateY(-2px); }}
  </style>
</head>
<body>

  <div class="loading" id="loading">
    <div class="spinner"></div>
    <div style="color:var(--text);font-size:14px;font-weight:500;">Chargement des données…</div>
  </div>

  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="logo">
      <div class="logo-icon"><i data-feather="box" style="width:20px; height:20px; color:white;"></i></div>
      <h1>Dabang</h1>
    </div>
    <nav class="sidebar-nav">
      <a href="/"><i data-feather="settings"></i> Générateur</a>
      <a href="/dashboard"><i data-feather="pie-chart"></i> Tableau de bord</a>
      <a href="/economy" class="active"><i data-feather="trending-up"></i> Analyse d'Économie</a>
    </nav>
    <div style="flex:1;"></div>
    <div class="sidebar-cta">
      <div class="cta-icon" style="margin-bottom: 8px;"><i data-feather="moon" style="width:24px; height:24px;"></i></div>
      <h3>Dark Mode</h3>
      <p>Basculez entre le thème clair et sombre</p>
      <button class="btn-theme" onclick="toggleTheme()">Changer de thème</button>
    </div>
  </aside>

  <!-- Main Content -->
  <div class="main-wrapper">
    
    <!-- Topbar -->
    <header class="topbar">
      <div class="page-title">Analyse Détaillée</div>
      <div class="topbar-right">
        <div style="display:flex; gap:12px; align-items:center;">
          <span id="cache-status-badge" style="font-size:12px; padding:6px 12px; border-radius:20px; background:var(--surface2); border:1px solid var(--border); color:var(--text-muted);">
            Cache: <b id="cache-time">Calcul…</b>
          </span>
          <button class="btn-theme" style="width:auto; padding:8px 16px; margin:0; display:flex; align-items:center; gap:8px;" onclick="refreshCache()">
            <i data-feather="refresh-cw" style="width:14px; height:14px;"></i> Actualiser les données
          </button>
        </div>
        <button id="btn-export" class="btn-export" onclick="exportData()" style="display:none;">
          <i data-feather="download" style="width:16px; height:16px;"></i>
          Exporter CSV
        </button>
        <div class="profile">
          <div class="profile-img"><i data-feather="user" style="width:20px; height:20px;"></i></div>
          <div class="profile-info">
            <span class="profile-name">Admin</span>
            <span class="profile-role" id="db-badge">Base de données</span>
          </div>
        </div>
      </div>
    </header>

    <!-- Content Area -->
    <main class="content-area">
      
      <!-- Filters Card -->
      <div class="card">
        <div class="card-title" style="cursor:pointer; display:flex; justify-content:space-between; align-items:center;" onclick="document.getElementById('filter-body').style.display = document.getElementById('filter-body').style.display === 'none' ? 'block' : 'none'; this.querySelector('svg').style.transform = document.getElementById('filter-body').style.display === 'none' ? 'rotate(180deg)' : 'rotate(0deg)';">
          <span>Filtres Globaux</span>
          <i data-feather="chevron-up" style="transition: transform 0.2s;"></i>
        </div>
        <div id="filter-body" style="display:block;">
          <div class="filters-grid">
          <div class="field">
            <label>Société</label>
            <select id="f-societe"><option value="">Toutes les sociétés</option></select>
          </div>
          <div class="field">
            <label>Date (JJ/MM/AAAA)</label>
            <input type="text" id="f-date" placeholder="ex: 31/12/2025" />
          </div>
          <div class="field">
            <label>Granularité</label>
            <select id="f-gran">
              <option value="monthly">Mensuelle</option>
              <option value="daily">Journalière</option>
              <option value="yearly">Annuelle</option>
            </select>
          </div>
          <div class="field">
            <label>Année début</label>
            <input type="text" id="f-year-debut" placeholder="ex: 2025" />
          </div>
          <div class="field">
            <label>ID</label>
            <input type="number" id="f-asset-id" placeholder="ex: 34473"/>
          </div>
          <div class="field">
            <label>Nom / Code</label>
            <input type="text" id="f-asset-search" placeholder="Recherche…"/>
          </div>
        </div>
        
        <div style="border-top: 1px solid var(--border); padding-top: 16px; margin-bottom: 16px;">
          <div class="field" style="max-width: 300px;">
            <label style="margin-bottom:4px;">Filtrer les Catégories <span style="font-size:10px;font-weight:normal;">(Maintenez CTRL pour choix multiple)</span></label>
            <select id="f-change-filter" multiple size="5" style="height: auto; padding: 6px;" onchange="filterSidebarCategories()">
              <option value="all">Toutes les catégories</option>
              <option value="modified" selected>Uniquement modifiées</option>
              <option value="unmodified">Uniquement non-modifiées</option>
              <option value="real">Catégories réelles (BD)</option>
              <option value="virtual">Catégories virtuelles</option>
            </select>
            <select id="f-cats" style="display:none;"></select>
          </div>
          <div class="cat-tags" id="cat-tags"></div>
        </div>
        
        <button class="btn-apply" onclick="loadData()">Actualiser l'Analyse</button>
        </div>
      </div>

      <!-- Total Saving Block -->
      <div class="total-block">
        <div>
          <h2 style="font-size:20px; font-weight:700; color:var(--text); margin-bottom:4px;">Écart Total sur la période</h2>
          <div id="period-text" style="font-size:13px; color:var(--text-muted);">Toutes les dates</div>
        </div>
        <div id="total-saving" style="font-size:36px; font-weight:700;">—</div>
      </div>

      <!-- Detail Table Card -->
      <div class="card">
        <div class="card-title">Détail par Société et Catégorie</div>
        <div class="table-wrap">
          <table id="economy-table">
            <thead><tr>
              <th>Société</th>
              <th>Catégorie</th>
              <th>Nb Immo</th>
              <th>Valeur Brute</th>
              <th>Amorti Réel</th>
              <th>Amorti Estimé</th>
              <th>Écart Global</th>
              <th>Courant Réel</th>
              <th>Courant Estimé</th>
            </tr></thead>
            <tbody id="economy-tbody"></tbody>
          </table>
        </div>
      </div>

    </main>
  </div>

  <script>
    // Theme toggler logic
    function toggleTheme() {{
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    }}
    if (localStorage.getItem('theme') === 'dark') {{
      document.documentElement.setAttribute('data-theme', 'dark');
    }}
  </script>

{script_content}

<script>
async function refreshCache() {{
  const btn = document.querySelector('button[onclick="refreshCache()"]');
  if (btn) btn.disabled = true;
  await fetch('/api/refresh_cache', {{ method: 'POST' }});
  pollCacheStatus();
}}

async function pollCacheStatus() {{
  const res = await fetch('/api/cache_status');
  const data = await res.json();
  const badge = document.getElementById('cache-time');
  const btn = document.querySelector('button[onclick="refreshCache()"]');
  if (badge) {{
    if (data.is_loading) {{
      badge.textContent = 'Actualisation en cours…';
      badge.style.color = 'var(--warn)';
      if (btn) btn.disabled = true;
      setTimeout(pollCacheStatus, 2000);
    }} else {{
      badge.textContent = data.last_update + ' (' + data.assets_count + ' immo)';
      badge.style.color = 'var(--ok)';
      if (btn) btn.disabled = false;
    }}
  }}
}}
window.addEventListener('DOMContentLoaded', () => {{
  pollCacheStatus();
}});
</script>
</body>
</html>"""

with open('templates/economy.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
