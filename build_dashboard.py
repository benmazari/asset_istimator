import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

script_match = re.search(r'(<script>\s*feather\.replace\(\);.*?</script>)', content, re.DOTALL)
if not script_match:
    # fallback to PALETTE array
    script_match = re.search(r'(<script>\s*const PALETTE.*?</script>)', content, re.DOTALL)
if not script_match:
    raise Exception('Main application script tag not found')
script_content = script_match.group(1)

new_html = f"""<!DOCTYPE html>
<html lang="fr" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Amortissement — Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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

    /* ── KPIs ── */
    .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
    .kpi {{
      background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 24px; position: relative; overflow: hidden; box-shadow: var(--shadow);
    }}
    .kpi::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }}
    .kpi.blue::before {{ background: var(--accent); }}
    .kpi.purple::before {{ background: #8b5cf6; }}
    .kpi.green::before {{ background: var(--ok); }}
    .kpi.orange::before {{ background: var(--warn); }}
    
    .kpi .kpi-label {{ font-size: 11px; font-weight: 600; color: var(--text-muted); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 12px; }}
    .kpi .kpi-val {{ font-size: 28px; font-weight: 700; color: var(--text); letter-spacing: -0.5px; }}
    .kpi .kpi-sub {{ font-size: 12px; color: var(--text-muted); margin-top: 6px; font-weight: 500; }}
    
    .kpi.blue .kpi-val {{ color: var(--accent); }}
    .kpi.purple .kpi-val {{ color: #8b5cf6; }}
    .kpi.green .kpi-val {{ color: var(--ok); }}
    .kpi.orange .kpi-val {{ color: var(--warn); }}

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
    
    /* ── Charts ── */
    .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
    .chart-wrap {{ position: relative; height: 320px; }}
    
    /* ── Category Cards ── */
    .cat-cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}
    .cat-count-card {{
      background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px;
      display: flex; flex-direction: column; gap: 8px; transition: all .2s; box-shadow: var(--shadow);
    }}
    .cat-count-card:hover {{ transform: translateY(-2px); border-color: var(--accent); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }}
    .cat-count-name {{ font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .cat-count-val {{ font-size: 20px; font-weight: 700; color: var(--accent); }}

    /* ── Loading ── */
    .loading {{
      display: none; position: fixed; inset: 0; background: rgba(255,255,255,0.7);
      backdrop-filter: blur(4px); z-index: 100; align-items: center; justify-content: center; flex-direction: column; gap: 14px;
    }}
    [data-theme="dark"] .loading {{ background: rgba(15,17,23,0.7); }}
    .loading.show {{ display: flex; }}
    .spinner {{ width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }}

    /* Scenario */
    .scenario-panel {{ display: none; }}
    .scenario-panel.show {{ display: block; }}
    .saving-banner {{ padding: 16px 20px; border-radius: 12px; font-size: 14px; font-weight: 500; text-align: center; margin-bottom: 24px; }}
    .saving-banner.pos {{ background: rgba(34,197,94,.1); color: #16a34a; border: 1px solid rgba(34,197,94,.2); }}
    .saving-banner.neg {{ background: rgba(239,68,68,.1); color: #dc2626; border: 1px solid rgba(239,68,68,.2); }}

    .error-banner {{ background: rgba(239,68,68,.1); border: 1px solid var(--err); border-radius: 10px; padding: 14px 20px; color: var(--err); font-size: 14px; margin-bottom: 24px; display: none; }}

    @media (max-width: 1024px) {{
      .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
      .charts-grid {{ grid-template-columns: 1fr; }}
    }}
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
      <a href="/dashboard" class="active"><i data-feather="pie-chart"></i> Tableau de bord</a>
      <a href="/economy"><i data-feather="trending-up"></i> Analyse d'Économie</a>
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
      <div class="page-title">Tableau de bord</div>
      <div class="topbar-right">
        <div style="display:flex; gap:12px; align-items:center;">
          <span id="cache-status-badge" style="font-size:12px; padding:6px 12px; border-radius:20px; background:var(--surface2); border:1px solid var(--border); color:var(--text-muted);">
            Cache: <b id="cache-time">Calcul…</b>
          </span>
          <button class="btn-theme" style="width:auto; padding:8px 16px; margin:0; display:flex; align-items:center; gap:8px;" onclick="refreshCache()">
            <i data-feather="refresh-cw" style="width:14px; height:14px;"></i> Actualiser les données
          </button>
        </div>
        <div class="search-bar">
          <i data-feather="search" style="width:16px; height:16px; color:var(--text-muted);"></i>
          <input type="text" placeholder="Recherche rapide..." />
        </div>
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
      
      <div style="display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
          <h2 id="overview-company" style="font-size:22px; font-weight:700; color:var(--text); margin-bottom:4px;">Toutes les sociétés</h2>
          <span id="overview-period" style="font-size:14px; color:var(--text-muted);"></span>
        </div>
      </div>

      <div class="error-banner" id="err-banner"></div>
      
      <!-- Scenario panel -->
      <div class="scenario-panel" id="scenario-panel">
        <div class="saving-banner" id="sc-saving"></div>
      </div>

      <!-- Expert KPIs -->
      <div class="kpi-row">
        <div class="kpi blue">
          <div class="kpi-label">Valeur Brute Totale</div>
          <div class="kpi-val" id="k-pv">—</div>
          <div class="kpi-sub">Valeur d'acquisition globale</div>
        </div>
        <div class="kpi purple">
          <div class="kpi-label">Total Réel Amorti</div>
          <div class="kpi-val" id="k-real">—</div>
          <div class="kpi-sub">Montant cumulatif amorti</div>
        </div>
        <div class="kpi orange">
          <div class="kpi-label">Taux d'Amortissement</div>
          <div class="kpi-val" id="k-taux">—</div>
          <div class="kpi-sub">Niveau de vétusté global</div>
        </div>
        <div class="kpi green">
          <div class="kpi-label">Écart (Réel − Estimé)</div>
          <div class="kpi-val" id="k-gap">—</div>
          <div class="kpi-sub">Sur/Sous amortissement total</div>
        </div>
      </div>

      <!-- Filters Card -->
      <div class="card">
        <div class="card-title" style="cursor:pointer; display:flex; justify-content:space-between; align-items:center;" onclick="document.getElementById('filter-body').style.display = document.getElementById('filter-body').style.display === 'none' ? 'block' : 'none'; this.querySelector('svg').style.transform = document.getElementById('filter-body').style.display === 'none' ? 'rotate(180deg)' : 'rotate(0deg)';">
          <span>Filtres du Tableau de bord</span>
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
        
        <button class="btn-apply" onclick="loadDashboard()">Actualiser le Dashboard</button>
        </div>
      </div>

      <!-- Charts row 1 -->
      <div class="charts-grid">
        <div class="card">
          <div class="card-title">Écart (Réel − Estimé) par catégorie</div>
          <div class="chart-wrap"><canvas id="chart-ecart"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">
            Réel vs Estimé par catégorie 
            <span style="font-size: 11px; padding: 4px 10px; background: var(--surface2); border: 1px solid var(--border); border-radius: 20px; color: var(--text-muted);" id="badge-date">toutes dates</span>
          </div>
          <div class="chart-wrap"><canvas id="chart-gap"></canvas></div>
        </div>
      </div>

      <!-- Matrix table for Company -->
      <div class="card">
        <div class="card-title">Analyse par Société</div>
        <div class="table-wrap">
          <table id="company-table">
            <thead><tr>
              <th>Société</th>
              <th>Nombre Immo</th>
              <th>Valeur Brute</th>
              <th>Réel amorti</th>
              <th>Estimé</th>
              <th>Écart (Réel - Estimé)</th>
              <th>Courant Réel</th>
              <th>Courant Estimé</th>
            </tr></thead>
            <tbody id="company-tbody"></tbody>
          </table>
        </div>
      </div>

      <!-- Category Asset Count Cards (Expandable) -->
      <div class="card" onclick="toggleCatCards()" style="cursor:pointer; display:flex; flex-direction: row; justify-content:space-between; align-items:center; transition:background-color 0.2s;">
        <div>
          <div style="font-size:12px;font-weight:600;color:var(--text-muted);letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px;">Total des Immobilisations</div>
          <div id="k-assets-total" style="font-size:28px;font-weight:700;color:var(--accent);">—</div>
        </div>
        <div id="cat-cards-icon" style="font-size:13px; font-weight: 600; color:var(--text); padding:10px 16px; border-radius:12px; background:var(--surface2); border: 1px solid var(--border);">Voir par catégorie ▼</div>
      </div>
      <div class="cat-cards-grid" id="cat-cards" style="display:none;"></div>

      <!-- Gap table -->
      <div class="card">
        <div class="card-title">Détail par catégorie</div>
        <div class="table-wrap">
          <table id="gap-table">
            <thead><tr>
              <th>Catégorie</th>
              <th>Réel amorti</th>
              <th>Estimé</th>
              <th>Écart</th>
              <th>Nb immo</th>
              <th title="method_number/12 depuis la BD">Ancienne durée (ans)</th>
              <th title="Durée configurée">Nouvelle durée (ans)</th>
              <th>Courant Réel</th>
              <th>Courant Estimé</th>
              <th>Économie / période</th>
            </tr></thead>
            <tbody id="gap-tbody"></tbody>
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

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

