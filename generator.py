"""
generator.py - Shared generation logic.

Strategy:
  1. Fetch all asset master data + real depreciation lines in TWO fast queries.
  2. Compute the monthly OR daily amortization schedule in Python.
  3. Export to Excel/CSV.

Granularity options:
  'monthly' — one row per end-of-month  (original behaviour)
  'daily'   — one row per calendar day
  'both'    — produces two result sets (monthly + daily) exported as separate sheets

This avoids the slow CTE + generate_series approach that hangs on large datasets.
"""

import os
import sys
import warnings
import math
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

import pandas as pd
import psycopg2.extras

warnings.filterwarnings("ignore", category=FutureWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from db import get_connection
from exporter import export_to_excel, export_to_csv


# ── Virtual Categories Mapping ────────────────────────────────────────────────
VIRTUAL_CATEGORIES = {
    "Bâtiments d'habitation": {
        "years": 50,
        "asset_ids": {245131, 245132, 245133}
    },
    "PRESSES ET COMPRESSEUR": {
        "years": 10,
        "asset_ids": {246689, 247684, 247904}
    }
}

# Flatten for O(1) lookup
VIRTUAL_OVERRIDES = {}
for _lbl, _data in VIRTUAL_CATEGORIES.items():
    for _aid in _data["asset_ids"]:
        VIRTUAL_OVERRIDES[_aid] = {"label": _lbl, "years": _data["years"]}


# ── SQL: fetch asset master data ──────────────────────────────────────────────


ASSET_SQL = """
SELECT
    aaat.id                     AS id_immo,
    aaat.code                   AS "Référence",
    societe_comptable.name      AS "Société",
    aaat.name                   AS "Nom immobilisation",
    aaat.purchase_date          AS "Date d'acquisition",
    aaat.date_comptabilisation  AS "Date début d'amortissement",
    aaaf.name                   AS "Localisation",
    gee.name                    AS "Equipement",
    aaat.unit_price             AS "Prix unitaire",
    aaat.costs                  AS "Autres frais",
    aaat.purchase_value         AS "Valeur brute",
    aaat.tva_acquisition        AS "TVA d'acquisition",
    aaat.venal_value            AS "Valeur vénale",
    aaat.expert_value           AS "Valeur d'expertise",
    CONCAT(acck.name, ' (', rc_cout.name, ')') AS "Centre de coût",
    aaat.state                  AS "Statut",
    aaat.num_serie              AS "Numéro de série",
    compte_immo.code || ' ' || compte_immo.name
        || ' (' || compte_immo_company.name || ')'
        AS "Compte d'immobilisation",
    compte_dep.code || ' ' || compte_dep.name
        || ' (' || compte_dep_company.name || ')'
        AS "Compte de dépréciation",
    compte_exp.code || ' ' || compte_exp.name
        || ' (' || compte_exp_company.name || ')'
        AS "Compte de dépréciation (charge)",
    aac.name                    AS "Catégorie d'immobilisation",
    aaat.dossier_complet        AS "Dossier complet",
    aaat.fournisseur            AS "Référence facture fournisseur",
    aaat.venal_value_date       AS "Date de valeur",
    aaat.type_sortie            AS "Type sortie",
    aaat.date_cession           AS "Date sortie",
    aaat.fournisseur_str        AS "Fournisseur",
    res_currency.name           AS "Devise",
    fv.name                     AS "Véhicule",
    (hr_employee.name_related || ' ' || hr_employee.firstname)
        AS "Employé affecté",
    ROUND((COALESCE(aaat.method_number, aac.method_number)::numeric / 12.0), 2) AS "Durée d'amortissement (Odoo)",
    aaat.old_id                 AS "Ancien ID"
FROM account_asset_asset aaat
JOIN account_asset_category aac ON aac.id = aaat.category_id
LEFT JOIN gmao_equipment_equipment gee     ON aaat.equipement_id = gee.id
LEFT JOIN fleet_vehicle fv                 ON aaat.vehicle_id = fv.id
LEFT JOIN account_asset_affectation aaaf   ON aaat.affectation_id = aaaf.id
LEFT JOIN hr_employee                      ON aaat.employee_affected_id = hr_employee.id
LEFT JOIN res_currency                     ON aaat.currency_id = res_currency.id
LEFT JOIN res_company societe_comptable    ON societe_comptable.id = aaat.company_id
LEFT JOIN asset_center_cout acck           ON acck.id = aaat.center_cout_id
LEFT JOIN res_company rc_cout              ON acck.company_id = rc_cout.id
LEFT JOIN account_account compte_immo      ON compte_immo.id = aaat.account_asset_id
LEFT JOIN res_company compte_immo_company  ON compte_immo_company.id = compte_immo.company_id
LEFT JOIN account_account compte_dep       ON compte_dep.id = aaat.account_depreciation_id
LEFT JOIN res_company compte_dep_company   ON compte_dep_company.id = compte_dep.company_id
LEFT JOIN account_account compte_exp       ON compte_exp.id = aaat.account_expense_depreciation_id
LEFT JOIN res_company compte_exp_company   ON compte_exp_company.id = compte_exp.company_id
WHERE (aac.id = ANY(%s) {virtual_filter})
  {asset_filter}
  {societe_filter}
  {year_debut_filter}
  {search_filter}
ORDER BY aaat.id
"""

# ── SQL: fetch real depreciation lines ───────────────────────────────────────

LINES_SQL = """
SELECT
    asset_id,
    depreciation_date,
    depreciated_value,
    amount,
    remaining_value,
    name,
    type,
    move_check
FROM account_asset_depreciation_line
WHERE asset_id = ANY(%s)
  {date_filter}
"""


def _last_day_of_month(d: date) -> date:
    """Return the last day of the month for date d."""
    return (d.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)


def _compute_schedule(asset_row: dict, years: int) -> list[dict]:
    """
    Compute the MONTHLY estimated amortization schedule for one asset.
    Returns a list of dicts — one entry per end-of-month.

    Uses years * 365 as the fixed denominator (standard French linear
    accounting convention — ignores leap years) so results match
    reference files built on the same convention.
    """
    start: date = asset_row["Date début d'amortissement"]
    if start is None:
        return []

    purchase_value = float(asset_row["Valeur brute"] or 0)

    end_date: date = (start + relativedelta(years=years)) - timedelta(days=1)
    # Standard French accounting: fixed 365-day year, no leap-year adjustment
    total_days = years * 365
    daily_amount = purchase_value / total_days

    rows = []
    cum_estimated = 0.0
    current = start

    while current <= end_date:
        dep_date = _last_day_of_month(current)
        if dep_date > end_date:
            dep_date = end_date

        days_in_period = (dep_date - current).days + 1
        base_amount = daily_amount * days_in_period

        # Last month: adjust to avoid floating-point overshoot
        if dep_date >= end_date:
            base_amount = purchase_value - cum_estimated

        base_amount = max(0.0, base_amount)
        cum_estimated += base_amount
        remaining = max(0.0, purchase_value - cum_estimated)

        rows.append({
            "dep_date":             dep_date,
            "base_amount":          round(base_amount, 6),
            "cum_estimated":        round(cum_estimated, 6),
            "remaining_estimated":  round(remaining, 6),
            "days_in_period":       days_in_period,
        })

        current = (dep_date.replace(day=1) + relativedelta(months=1))

    return rows


def _compute_schedule_daily(asset_row: dict, years: int) -> list[dict]:
    """
    Compute the DAILY estimated amortization schedule for one asset.
    Returns a list of dicts — one entry per calendar day from start to end_date.

    Each day carries:
        dep_date            — the calendar date
        base_amount         — daily_amount  (= purchase_value / (years * 365))
                              Last day is adjusted to avoid floating-point drift.
        cum_estimated       — running cumulative depreciation up to and including this day
        remaining_estimated — purchase_value - cum_estimated (floor 0)
        days_in_period      — always 1 for daily schedule

    Uses years * 365 as fixed denominator (standard French accounting convention).
    """
    start: date = asset_row["Date début d'amortissement"]
    if start is None:
        return []

    purchase_value = float(asset_row["Valeur brute"] or 0)

    end_date: date = (start + relativedelta(years=years)) - timedelta(days=1)
    # Standard French accounting: fixed 365-day year, no leap-year adjustment
    total_days = years * 365
    if total_days <= 0:
        return []

    daily_amount = purchase_value / total_days

    rows = []
    cum_estimated = 0.0
    current = start

    while current <= end_date:
        if current == end_date:
            # Last day: absorb any floating-point remainder
            base_amount = max(0.0, purchase_value - cum_estimated)
        else:
            base_amount = daily_amount

        cum_estimated += base_amount
        remaining = max(0.0, purchase_value - cum_estimated)

        rows.append({
            "dep_date":             current,
            "base_amount":          round(base_amount, 6),
            "cum_estimated":        round(cum_estimated, 6),
            "remaining_estimated":  round(remaining, 6),
            "days_in_period":       1,
        })

        current += timedelta(days=1)

    return rows


def _compute_schedule_yearly(asset_row: dict, years: int) -> list[dict]:
    """
    Compute the YEARLY estimated amortization schedule for one asset.
    Returns one row per calendar year — the annual depreciation amount
    and the running cumulative at year-end.
    Also sums the days_in_period across all months in the year.
    """
    monthly = _compute_schedule(asset_row, years)
    if not monthly:
        return []

    by_year: dict = {}
    for row in monthly:
        yr = row["dep_date"].year
        if yr not in by_year:
            by_year[yr] = {"sum_base": 0.0, "last_cum": 0.0, "last_rem": 0.0,
                           "last_date": None, "sum_days": 0}
        by_year[yr]["sum_base"]  += row["base_amount"]
        by_year[yr]["last_cum"]   = row["cum_estimated"]
        by_year[yr]["last_rem"]   = row["remaining_estimated"]
        by_year[yr]["last_date"]  = row["dep_date"]
        by_year[yr]["sum_days"]  += row.get("days_in_period", 0)

    result = []
    for yr in sorted(by_year):
        d = by_year[yr]
        result.append({
            "dep_date":            d["last_date"],
            "base_amount":         round(d["sum_base"], 6),
            "cum_estimated":       round(d["last_cum"],  6),
            "remaining_estimated": round(d["last_rem"],  6),
            "days_in_period":      d["sum_days"],
        })
    return result


def _last_day_of_month(d: date) -> date:
    """Return the last calendar day of the month containing `d`."""
    from calendar import monthrange
    return date(d.year, d.month, monthrange(d.year, d.month)[1])


def generate(
    categories: list[dict],
    output_format: str,
    output_dir: str,
    asset_id: int = None,
    societe: str = None,
    dep_date: str = None,
    granularity: str = "monthly",   # 'monthly' | 'daily' | 'both' | 'yearly'
    from_date: date = None,         # only emit rows with dep_date >= from_date
    as_of_date: date = None,        # snapshot: emit only the row matching this date
    log_fn=print,
    progress_fn=None,
    year_debut: int = None,
    asset_search: str = None,
    non_amortie: bool = False,
    year_debut_type: str = "start_date",
) -> str | None:
    """
    Main generation function.

    Args:
        categories:    List of dicts with 'ids' and 'years' (and 'label').
        output_format: 'excel' | 'csv' | 'both'
        output_dir:    Directory for output files.
        asset_id:      Optional single asset ID to filter (for testing).
        societe:       Optional company name to filter.
        dep_date:      Optional depreciation date (YYYY-MM-DD) to filter lines.
        granularity:   'monthly' | 'daily' | 'both' | 'yearly'
        from_date:     Only emit rows with dep_date >= from_date (full schedule
                       still computed so cumulative values remain correct).
        as_of_date:    Snapshot date — emit ONLY the row whose dep_date matches
                       this date (snapped to period end based on granularity).
                       Overrides from_date when set.
        log_fn:        Logging callback.
        progress_fn:   Optional progress callback(done, total).

    Returns:
        Path to primary output file, or None on error.
    """
    import yaml
    cfg_path = os.path.join(SCRIPT_DIR, "config.yaml")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Load all categories from config to populate VIRTUAL_OVERRIDES globally
    all_cats = cfg.get("categories", []) or []
    has_virtual = any(c.get("is_virtual") for c in all_cats)
    if not has_virtual:
        all_cats = list(all_cats) + [
            {"ids": [-1], "label": "Bâtiments d'habitation", "years": 50, "is_virtual": True, "asset_ids": [245131, 245132, 245133]},
            {"ids": [-2], "label": "PRESSES ET COMPRESSEUR", "years": 10, "is_virtual": True, "asset_ids": [246689, 247684, 247904]}
        ]

    global VIRTUAL_OVERRIDES
    VIRTUAL_OVERRIDES = {}
    for c in all_cats:
        if c.get("is_virtual"):
            lbl = c.get("label")
            yrs = c.get("years", 10)
            for aid in c.get("asset_ids", []):
                VIRTUAL_OVERRIDES[aid] = {"label": lbl, "years": yrs}

    conn = get_connection(cfg["database"])
    results = {}
    output_file = None

    try:
        for cat in categories:
            # Handle both formats: new `ids` + `label`, or old `pattern`
            if "ids" in cat:
                cat_ids = cat["ids"]
                label   = cat.get("label", "Categorie")
            else:
                # Fallback for old pattern format
                label = cat["pattern"].replace("%", "").strip()
                cat_ids = [] # We'll need to fetch them if needed, but assuming user uses ids now.
            if "years" in cat:
                years = int(cat["years"])
            else:
                years = int(cat["months"]) / 12

            # ── 1. Fetch asset master rows ────────────────────────────────────
            v_aids = []
            for cid in cat_ids:
                for c in categories:
                    if c.get("is_virtual") and c["ids"][0] == cid:
                        v_aids.extend(c.get("asset_ids", []))
            virtual_filter = f"OR aaat.id = ANY(ARRAY{v_aids})" if v_aids else ""

            asset_filter = "AND aaat.id = %s" if asset_id else ""
            societe_filter = "AND societe_comptable.name = %s" if societe else ""
            date_col = "aaat.purchase_date" if year_debut_type == "purchase_date" else "aaat.date_comptabilisation"
            year_debut_filter = f"AND EXTRACT(YEAR FROM {date_col}) = %s" if year_debut else ""
            search_filter = "AND (aaat.code ILIKE %s OR aaat.name ILIKE %s)" if asset_search else ""
            sql = ASSET_SQL.format(
                virtual_filter=virtual_filter,
                asset_filter=asset_filter,
                societe_filter=societe_filter,
                year_debut_filter=year_debut_filter,
                search_filter=search_filter
            )

            params: list = [cat_ids]
            if asset_id:
                params.append(asset_id)
            if societe:
                params.append(societe)
            if year_debut:
                params.append(year_debut)
            if asset_search:
                s_param = f"%{asset_search}%"
                params.append(s_param)
                params.append(s_param)

            log_fn(f"Recuperation des immobilisations : {label} ...")
            if societe:
                log_fn(f"  Filtre societe : {societe}")
            if year_debut:
                log_fn(f"  Filtre annee debut : {year_debut}")
            if asset_search:
                log_fn(f"  Filtre recherche immo : {asset_search}")

            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql, params)
                asset_rows = [dict(r) for r in cur.fetchall()]

            total_assets = len(asset_rows)
            log_fn(f"  -> {total_assets} immobilisation(s) trouvee(s)")
            if not asset_rows:
                log_fn(f"  Aucune immobilisation pour '{label}', ignore.")
                continue

            asset_ids = [r["id_immo"] for r in asset_rows]

            # ── 2. Fetch real depreciation lines ──────────────────────────────
            log_fn("  Recuperation des lignes reelles ...")
            lines_index: dict[tuple, dict] = {}
            
            # If yearly granularity, we need to sum lines for the whole year.
            # If a snapshot date is provided, we still need the whole year's data for that year's row.
            
            fetch_all_years = (granularity == "yearly") or not (dep_date or as_of_date)
            
            if fetch_all_years:
                date_filter = ""
                lines_params: list = [asset_ids]
            else:
                _date_filter_val = dep_date or (as_of_date.strftime("%Y-%m-%d") if as_of_date else None)
                date_filter = "AND depreciation_date = %s" if _date_filter_val else ""
                lines_params = [asset_ids]
                if _date_filter_val:
                    lines_params.append(_date_filter_val)
            
            lines_sql = LINES_SQL.format(date_filter=date_filter)
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(lines_sql, lines_params)
                for line in cur.fetchall():
                    d_date = line["depreciation_date"]
                    aid = line["asset_id"]
                    
                    if granularity == "yearly":
                        # For yearly, we sum amounts by (asset, year)
                        key = (aid, date(d_date.year, 12, 31))
                        if key not in lines_index:
                            lines_index[key] = {
                                "amount": 0.0, 
                                "depreciated_value": 0.0, 
                                "remaining_value": 0.0,
                                "depreciation_date": None,
                                "name": "Total Annuel",
                                "type": "yearly_agg",
                                "move_check": True
                            }
                        lines_index[key]["amount"] += float(line["amount"] or 0)
                        # For cumulative values, we take the latest one in the year
                        if not lines_index[key]["depreciation_date"] or d_date > lines_index[key]["depreciation_date"]:
                            lines_index[key]["depreciation_date"] = d_date
                            lines_index[key]["depreciated_value"] = float(line["depreciated_value"] or 0)
                            lines_index[key]["remaining_value"]   = float(line["remaining_value"] or 0)
                    else:
                        key = (aid, d_date)
                        ld = dict(line)
                        # Cast decimals to floats for calculations and excel compat
                        for k in ["amount", "depreciated_value", "remaining_value"]:
                            if ld.get(k) is not None:
                                ld[k] = float(ld[k])
                        lines_index[key] = ld

            # ── 3. Compute schedules in Python ────────────────────────────────
            run_monthly = granularity in ("monthly", "both")
            run_daily   = granularity in ("daily",   "both")
            run_yearly  = granularity == "yearly"

            # Resolve the exact target dates from as_of_date
            target_monthly = target_daily = target_year = None
            if as_of_date:
                log_fn(f"  Filtre 'date de depreciation' : {as_of_date.isoformat()} (granularite: {granularity})")
                if run_monthly or (run_daily is False and run_yearly is False):
                    target_monthly = _last_day_of_month(as_of_date)
                if run_daily:
                    target_daily = as_of_date
                if run_yearly:
                    target_year = as_of_date.year
            elif from_date:
                log_fn(f"  Filtre 'a partir de' : {from_date.isoformat()}")

            log_fn(f"  Calcul des amortissements ({years} ans) — granularite: {granularity} ...")

            if "all_monthly_rows" not in locals():
                all_monthly_rows = {}
                all_daily_rows   = {}
                all_yearly_rows  = {}

            for i, asset in enumerate(asset_rows):
                eff_years = years
                eff_label = label
                asset_id_immo = asset["id_immo"]
                
                # Check for virtual category override
                if asset_id_immo in VIRTUAL_OVERRIDES:
                    eff_years = VIRTUAL_OVERRIDES[asset_id_immo]["years"]
                    eff_label = VIRTUAL_OVERRIDES[asset_id_immo]["label"]
                    asset["Catégorie d'immobilisation"] = eff_label

                # Avoid duplicate rows by skipping virtual overrides when processing their base standard categories
                if eff_label != label:
                    continue

                # Pre-compute daily rates for this asset
                pv        = float(asset.get("Valeur brute") or 0)
                old_yrs   = float(asset.get("Durée d'amortissement (Odoo)") or 0)
                daily_new = round(pv / (eff_years * 365), 10) if eff_years > 0 else None
                daily_old = round(pv / (old_yrs * 365), 10) if old_yrs > 0 else None

                # ── Monthly schedule ─────────────────────────────────────────
                if run_monthly:
                    if eff_label not in all_monthly_rows:
                        all_monthly_rows[eff_label] = []
                    for sched in _compute_schedule(asset, eff_years):
                        d = sched["dep_date"]
                        if as_of_date and d != target_monthly:
                            continue
                        if from_date and d < from_date:
                            continue
                        if non_amortie:
                            real_data = lines_index.get((asset["id_immo"], d), {})
                            real_cum = real_data.get("depreciated_value", 0)
                            if asset.get("Statut") == "close" or (real_cum and real_cum >= pv - 0.01):
                                continue
                        real = lines_index.get((asset["id_immo"], d), {})
                        all_monthly_rows[eff_label].append({
                            **asset,
                            "Durée d'amortissement (Excel)":    eff_years,
                            "Date de dépréciation":             d,
                            "Amortissement journalier (Odoo)":  daily_old,
                            "Amortissement journalier (estimé)": daily_new,
                            "Nom amortissement":                 real.get("name"),
                            "Type":                              real.get("type"),
                            "Montant déjà amorti réel":          real.get("depreciated_value"),
                            "Amortissement courant réel":        real.get("amount"),
                            "Période suivante réelle":           real.get("remaining_value"),
                            "Comptabilisé":                      real.get("move_check"),
                            "Amortissement courant estimé":      sched["base_amount"],
                            "Montant déjà amorti estimé":        sched["cum_estimated"],
                            "Période suivante estimée":          sched["remaining_estimated"],
                            "Écart (Réel - Estimé)":             round(float(real.get("amount") or 0.0) - float(sched["base_amount"] or 0.0), 2),
                        })

                # ── Daily schedule ───────────────────────────────────────────
                if run_daily:
                    if f"{eff_label} (Journalier)" not in all_daily_rows:
                        all_daily_rows[f"{eff_label} (Journalier)"] = []
                    for sched in _compute_schedule_daily(asset, eff_years):
                        d = sched["dep_date"]
                        if as_of_date and d != target_daily:
                            continue
                        if from_date and d < from_date:
                            continue
                        if non_amortie:
                            real_data = lines_index.get((asset["id_immo"], d), {})
                            real_cum = real_data.get("depreciated_value", 0)
                            if asset.get("Statut") == "close" or (real_cum and real_cum >= pv - 0.01):
                                continue
                        real = lines_index.get((asset["id_immo"], d), {})
                        all_daily_rows[f"{eff_label} (Journalier)"].append({
                            **asset,
                            "Durée d'amortissement (Excel)":     eff_years,
                            "Date de dépréciation":              d,
                            "Amortissement journalier (Odoo)":   daily_old,
                            "Amortissement journalier (estimé)": daily_new,
                            "Nom amortissement":                  real.get("name"),
                            "Type":                               real.get("type"),
                            "Montant déjà amorti réel":           real.get("depreciated_value"),
                            "Amortissement courant réel":         real.get("amount"),
                            "Période suivante réelle":            real.get("remaining_value"),
                            "Comptabilisé":                       real.get("move_check"),
                            "Amortissement journalier estimé":    sched["base_amount"],
                            "Montant déjà amorti estimé (cumulé)": sched["cum_estimated"],
                            "Période suivante estimée":           sched["remaining_estimated"],
                            "Écart (Réel - Estimé)":             round(float(real.get("amount") or 0.0) - float(sched["base_amount"] or 0.0), 2),
                        })

                # ── Yearly schedule ──────────────────────────────────────────
                if run_yearly:
                    if f"{eff_label} (Annuel)" not in all_yearly_rows:
                        all_yearly_rows[f"{eff_label} (Annuel)"] = []
                    for sched in _compute_schedule_yearly(asset, eff_years):
                        d = sched["dep_date"]
                        if as_of_date and d.year != target_year:
                            continue
                        if from_date and d < from_date:
                            continue
                        if non_amortie:
                            real_data = lines_index.get((asset["id_immo"], d), {})
                            real_cum = real_data.get("depreciated_value", 0)
                            if asset.get("Statut") == "close" or (real_cum and real_cum >= pv - 0.01):
                                continue
                        real = lines_index.get((asset["id_immo"], d), {})
                        all_yearly_rows[f"{eff_label} (Annuel)"].append({
                            **asset,
                            "Durée d'amortissement (Excel)":     eff_years,
                            "Date de dépréciation":              d,
                            "Amortissement journalier (Odoo)":   daily_old,
                            "Amortissement journalier (estimé)": daily_new,
                            "Nom amortissement":                  real.get("name"),
                            "Type":                               real.get("type"),
                            "Montant déjà amorti réel":           real.get("depreciated_value"),
                            "Amortissement courant réel":         real.get("amount"),
                            "Période suivante réelle":            real.get("remaining_value"),
                            "Comptabilisé":                       real.get("move_check"),
                            "Amortissement annuel estimé":        sched["base_amount"],
                            "Montant déjà amorti estimé":         sched["cum_estimated"],
                            "Période suivante estimée":           sched["remaining_estimated"],
                            "Écart (Réel - Estimé)":             round(float(real.get("amount") or 0.0) - float(sched["base_amount"] or 0.0), 2),
                        })

                if progress_fn:
                    progress_fn(i + 1, total_assets)

        conn.close()

        # Build results globally after the loop finishes
        if "all_monthly_rows" in locals():
            if run_monthly:
                for lbl, rws in all_monthly_rows.items():
                    if rws:
                        results[lbl] = pd.DataFrame(rws)
                        log_fn(f"  -> {len(rws):,} lignes mensuelles pour '{lbl}'")
            if run_daily:
                for lbl, rws in all_daily_rows.items():
                    if rws:
                        results[lbl] = pd.DataFrame(rws)
                        log_fn(f"  -> {len(rws):,} lignes journalieres pour '{lbl}'")
            if run_yearly:
                for lbl, rws in all_yearly_rows.items():
                    if rws:
                        results[lbl] = pd.DataFrame(rws)
                        log_fn(f"  -> {len(rws):,} lignes annuelles pour '{lbl}'")

        if not results:
            log_fn("[ERREUR] Aucune immobilisation trouvee pour les criteres selectionnes.")
            return None

        # ── 4. Export ─────────────────────────────────────────────────────────
        os.makedirs(output_dir, exist_ok=True)
        log_fn("Export en cours ...")

        if output_format in ("excel", "both"):
            output_file = export_to_excel(results, output_dir)
            log_fn(f"Fichier Excel cree : {output_file}")

        if output_format in ("csv", "both"):
            paths = export_to_csv(results, output_dir)
            if not output_file and paths:
                output_file = paths[0]
            log_fn(f"CSV : {len(paths)} fichier(s) cree(s)")

        log_fn("Generation terminee avec succes !")

    except Exception as e:
        log_fn(f"[ERREUR] {e}")
        try:
            conn.close()
        except Exception:
            pass
        output_file = None

    return output_file
