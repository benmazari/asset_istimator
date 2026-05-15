import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

script_match = re.search(r'(<script>\s*feather\.replace\(\);.*?</script>)', content, re.DOTALL)
if not script_match:
    # fallback to state
    script_match = re.search(r'(<script>\s*// ── State.*?</script>)', content, re.DOTALL)
if not script_match:
    raise Exception('Main application script tag not found')
script_content = script_match.group(1)

new_html = f"""<!DOCTYPE html>
<html lang="fr" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Amortissement — Générateur</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
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
      display: grid; grid-template-columns: 360px 1fr; gap: 24px;
    }}
    
    @media (max-width: 1024px) {{
      .content-area {{ grid-template-columns: 1fr; }}
    }}

    /* ── Cards ── */
    .card {{
      background: var(--surface);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
      overflow: hidden;
      display: flex; flex-direction: column;
    }}
    .card-title {{
      padding: 20px 24px 16px;
      font-size: 15px; font-weight: 600; color: var(--text);
      display: flex; align-items: center; justify-content: space-between;
    }}
    .card-body {{ padding: 0 24px 24px; flex: 1; }}

    /* ── Form Fields ── */
    .field {{ display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }}
    .field:last-child {{ margin-bottom: 0; }}
    label {{ font-size: 12px; font-weight: 600; color: var(--text-muted); }}
    
    select, input[type=text] {{
      width: 100%;
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; color: var(--text);
      font-family: 'Inter', sans-serif; font-size: 13px;
      padding: 10px 14px; outline: none; transition: all .2s;
    }}
    select:focus, input[type=text]:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }}
    input::placeholder {{ color: var(--text-muted); opacity: 0.7; }}
    
    .sel-row {{ display: flex; gap: 8px; margin-bottom: 12px; }}
    .btn-xs {{
      font-size: 11px; font-weight: 600; padding: 6px 12px;
      border-radius: 8px; cursor: pointer; border: 1px solid var(--border);
      background: var(--surface2); color: var(--text-muted); transition: all .2s;
    }}
    .btn-xs:hover {{ background: var(--border); color: var(--text); }}

    /* Categories List */
    #cat-list {{ display: flex; flex-direction: column; gap: 8px; }}
    .cat-item {{
      display: flex; align-items: center; gap: 12px;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 10px 14px;
      cursor: pointer; transition: all .2s;
    }}
    .cat-item:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
    .cat-item.active {{ border-color: var(--accent); background: var(--accent-light); }}
    .cat-chk {{
      width: 20px; height: 20px; flex-shrink: 0;
      border: 2px solid var(--border); border-radius: 6px;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; transition: all .2s; color: white;
    }}
    .cat-item.active .cat-chk {{ background: var(--accent); border-color: var(--accent); }}
    .cat-name {{ flex: 1; font-size: 13px; font-weight: 500; }}
    .cat-yrs {{
      font-size: 11px; font-weight: 600; padding: 4px 10px;
      background: var(--surface2); border-radius: 20px; color: var(--text-muted);
    }}
    .cat-item.active .cat-yrs {{ background: white; color: var(--accent); }}

    /* ── Action Buttons ── */
    .btn-row {{ display: flex; gap: 12px; margin-top: 8px; }}
    .btn {{
      flex: 1; height: 44px; border-radius: 12px;
      font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600;
      cursor: pointer; border: none;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      transition: all .2s;
    }}
    .btn-primary {{ background: var(--accent); color: #fff; box-shadow: 0 4px 16px var(--accent-light); }}
    .btn-primary:hover {{ background: var(--accent-hover); transform: translateY(-2px); }}
    .btn-primary:disabled {{ opacity: .5; cursor: not-allowed; transform: none; box-shadow: none; }}
    .btn-outline {{ background: var(--surface); border: 2px solid var(--border); color: var(--text); }}
    .btn-outline:hover {{ border-color: var(--ok); color: var(--ok); }}
    .btn-outline:disabled {{ opacity: .4; cursor: not-allowed; }}

    /* ── Right Column Stats ── */
    .right-col {{ display: flex; flex-direction: column; gap: 24px; min-height: 0; }}
    .stats-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; flex-shrink: 0; }}
    .stat-card {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 20px;
      box-shadow: var(--shadow);
      display: flex; align-items: center; gap: 16px;
    }}
    .stat-icon {{
      width: 48px; height: 48px; border-radius: 12px;
      display: flex; align-items: center; justify-content: center; font-size: 20px;
    }}
    .stat-card:nth-child(1) .stat-icon {{ background: rgba(239, 68, 68, 0.1); color: #ef4444; }}
    .stat-card:nth-child(2) .stat-icon {{ background: rgba(245, 158, 11, 0.1); color: #f59e0b; }}
    .stat-card:nth-child(3) .stat-icon {{ background: rgba(34, 197, 94, 0.1); color: #22c55e; }}
    .stat-info {{ display: flex; flex-direction: column; }}
    .stat-val {{ font-size: 24px; font-weight: 700; color: var(--text); line-height: 1.2; }}
    .stat-lbl {{ font-size: 12px; color: var(--text-muted); font-weight: 500; }}

    /* ── Terminal/Log ── */
    .log-card {{ flex: 1; display: flex; flex-direction: column; min-height: 0; }}
    .log-terminal {{
      flex: 1; background: #0f1117; border-radius: 12px;
      padding: 16px; overflow-y: auto; font-family: 'JetBrains Mono', monospace;
      font-size: 12px; line-height: 1.6; color: #a1a1aa;
      border: 1px solid #27272a;
      height: 400px;
    }}
    .log-terminal::-webkit-scrollbar {{ width: 6px; }}
    .log-terminal::-webkit-scrollbar-thumb {{ background: #3f3f46; border-radius: 3px; }}

    .badge {{ font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 20px; }}
    .badge.running {{ background: rgba(79,125,243,.15); color: var(--accent); }}
    .badge.done    {{ background: rgba(34,197,94,.15); color: var(--ok); }}
    .badge.error   {{ background: rgba(239,68,68,.15); color: var(--err); }}
    .badge.ready   {{ background: var(--surface2); color: var(--text-muted); border: 1px solid var(--border); }}

    .ll {{ animation: fi .2s ease; }}
    @keyframes fi {{ from {{ opacity: 0; transform: translateY(4px); }} }}
    .lk {{ color: #4ade80; }}
    .le {{ color: #f87171; }}
    .lw {{ color: #fbbf24; }}
    .li {{ color: #a1a1aa; }}

    /* Loaders & Misc */
    .spinner {{
      width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff; border-radius: 50%; animation: spin .8s linear infinite; display: none;
    }}
    .spinner.on {{ display: inline-block; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    .mode-btn {{
      font-size: 11px; font-weight: 600; padding: 4px 10px;
      border-radius: 6px; cursor: pointer; border: none;
      background: transparent; color: var(--text-muted); transition: all .2s;
    }}
    .mode-btn.active {{ background: white; color: var(--accent); box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
    [data-theme="dark"] .mode-btn.active {{ background: var(--surface); }}
    .mode-btn-container {{
      display: flex; background: var(--surface2); border-radius: 8px; padding: 3px; gap: 2px;
      border: 1px solid var(--border);
    }}

    .warn-box {{
      padding: 12px 16px; border-radius: 10px;
      background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.2);
      font-size: 12px; color: var(--warn); display: none; margin-bottom: 16px;
    }}
  </style>
</head>
<body>

  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="logo">
      <div class="logo-icon"><i data-feather="box" style="width:20px; height:20px; color:white;"></i></div>
      <h1>Dabang</h1>
    </div>
    <nav class="sidebar-nav">
      <a href="/" class="active"><i data-feather="settings"></i> Générateur</a>
      <a href="/dashboard"><i data-feather="pie-chart"></i> Tableau de bord</a>
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
      <div class="page-title">Générateur d'Estimations</div>
      <div class="topbar-right">
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
      
      <!-- Left Column (Filters & Cats) -->
      <div class="left-col" style="display:flex; flex-direction:column; gap:24px;">
        
        <!-- Options Card -->
        <div class="card">
          <div class="card-title" style="cursor:pointer; display:flex; justify-content:space-between; align-items:center;" onclick="document.getElementById('filter-body').style.display = document.getElementById('filter-body').style.display === 'none' ? 'block' : 'none'; this.querySelector('svg').style.transform = document.getElementById('filter-body').style.display === 'none' ? 'rotate(180deg)' : 'rotate(0deg)';">
            <span>Configuration</span>
            <i data-feather="chevron-up" style="transition: transform 0.2s;"></i>
          </div>
          <div class="card-body" id="filter-body">
            
            <div class="field">
              <label for="sel-fmt">Format de sortie</label>
              <select id="sel-fmt">
                <option value="excel">Excel (.xlsx)</option>
                <option value="csv">CSV</option>
                <option value="both">Excel + CSV</option>
              </select>
            </div>

            <div class="field">
              <label for="sel-gran">Granularité du calcul</label>
              <select id="sel-gran" onchange="onGranChange(this.value)">
                <option value="monthly">Mensuelle</option>
                <option value="daily">Journalière</option>
                <option value="yearly">Annuelle</option>
                <option value="both">Mensuelle + Journalière</option>
              </select>
            </div>

            <div class="field">
              <label for="sel-societe">Société (optionnel)</label>
              <select id="sel-societe">
                <option value="">— Toutes —</option>
              </select>
            </div>

            <div class="field">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <label style="margin-bottom:0;" id="inp-asset-label">ID immobilisation</label>
                <div class="mode-btn-container">
                  <button id="mode-btn-id" class="mode-btn active" onclick="setAssetMode('id')">ID</button>
                  <button id="mode-btn-search" class="mode-btn" onclick="setAssetMode('search')">Code</button>
                </div>
              </div>
              <input type="text" id="inp-asset" placeholder="ex: 34473" />
            </div>

            <div class="field">
              <label for="inp-asof">Date de dépréciation (JJ/MM/AAAA)</label>
              <input type="text" id="inp-asof" placeholder="ex: 31/12/2025" />
            </div>

            <div class="field">
              <label for="inp-year-debut">Année début (AAAA)</label>
              <input type="text" id="inp-year-debut" placeholder="ex: 2025" />
            </div>

            <div class="warn-box" id="gran-warn">
              ⚠ La granularité journalière génère ~30× plus de lignes — peut être lente.
            </div>

            <div class="btn-row">
              <button class="btn btn-primary" id="btn-gen" onclick="startGen()">
                <span class="spinner" id="spin"></span>
                <i data-feather="play" style="width:16px; height:16px; display:inline-block; vertical-align:middle;"></i> <span id="btn-lbl">Générer</span>
              </button>
              <button class="btn btn-outline" id="btn-dl" disabled onclick="download()">
                <i data-feather="download" style="width:16px; height:16px;"></i> Exporter
              </button>
            </div>

          </div>
        </div>
      </div>

      <!-- Right Column (Stats & Log & Categories) -->
      <div class="right-col">
        
        <!-- Stats Row -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-icon"><i data-feather="folder" style="width:24px; height:24px;"></i></div>
            <div class="stat-info">
              <div class="stat-val" id="stat-cats">—</div>
              <div class="stat-lbl">Catégories</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><i data-feather="file-text" style="width:24px; height:24px;"></i></div>
            <div class="stat-info">
              <div class="stat-val" id="stat-rows">—</div>
              <div class="stat-lbl">Lignes générées</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><i data-feather="activity" style="width:24px; height:24px;"></i></div>
            <div class="stat-info">
              <div class="stat-val" id="stat-st" style="font-size: 18px;">En attente</div>
              <div class="stat-lbl">Statut</div>
            </div>
          </div>
        </div>

        <!-- Layout for Cats and Logs side-by-side on large screens, stacked on small -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; flex: 1; min-height: 0;">
          
          <!-- Categories Card -->
          <div class="card">
            <div class="card-title">
              Sélection Catégories
            </div>
            <div class="card-body" style="display: flex; flex-direction: column; overflow: hidden; padding-bottom: 20px;">
              <div class="field">
                <select id="sel-change-filter" onchange="filterIndexCategories(this.value)">
                  <option value="all">Toutes les catégories</option>
                  <option value="modified">Uniquement modifiées</option>
                  <option value="unmodified">Uniquement non-modifiées</option>
                </select>
              </div>
              <div class="sel-row">
                <button class="btn-xs" id="btn-all">Tout cocher</button>
                <button class="btn-xs" id="btn-none">Tout décocher</button>
              </div>
              <div id="cat-list" style="overflow-y: auto; flex: 1; padding-right: 4px; padding-bottom: 4px;">
                <div class="li" style="font-size:13px; padding: 10px;">Chargement…</div>
              </div>
            </div>
          </div>

          <!-- Log Card -->
          <div class="card log-card">
            <div class="card-title">
              Journal d'exécution
              <span class="badge ready" id="badge">Prêt</span>
            </div>
            <div class="card-body" style="display:flex; flex-direction:column; padding-top:0;">
              <div class="log-terminal" id="log-body">
                <span class="li">En attente de génération…</span>
              </div>
            </div>
          </div>

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
</body>
</html>"""

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
