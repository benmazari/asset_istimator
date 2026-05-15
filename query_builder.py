"""
query_builder.py — Builds the parameterized amortization SQL query.

The query is identical to the original SQL but:
  - Category ILIKE pattern is a psycopg2 %s parameter.
  - Amortization years uses make_interval(years => %s) — safe %s parameter.
  - The test filter (WHERE aaat.id = 34473) is optional via asset_id arg.
  - Assets in 'draft' state are excluded by default.
"""


def build_amortization_query(asset_ids: list = None) -> tuple:
    """
    Returns (sql, extra_params_tuple) ready for psycopg2 cursor.execute().

    Full params tuple must be assembled by caller as:
        (years, years, category_pattern, asset_ids_list) + extra_params
    where extra_params is () when asset_ids is None.

    Parameters bound in SQL order:
        1. years            (int)  - make_interval end_date
        2. years            (int)  - make_interval daily_amount
        3. category_pattern (str)  - ILIKE filter
        4. asset_ids        (list) - only when asset_ids is not None
    """

    asset_filter_sql   = "AND aaat.id = ANY(%s)" if asset_ids else ""
    asset_filter_param = (asset_ids,) if asset_ids else ()

    sql = f"""
WITH asset_base AS (
    SELECT
        aaat.*,
        (aaat.date_comptabilisation + make_interval(years => %s) - interval '1 day')::date
            AS end_date,

        aaat.purchase_value /
        NULLIF(
            (
                (aaat.date_comptabilisation + make_interval(years => %s) - interval '1 day')::date
                - aaat.date_comptabilisation
            )::numeric,
            0
        ) AS daily_amount

    FROM account_asset_asset aaat
    JOIN account_asset_category aac
        ON aac.id = aaat.category_id
    WHERE aac.name ILIKE %s
      AND aaat.state NOT IN ('close', 'draft')
      {asset_filter_sql}
),

schedule AS (
    SELECT
        ab.id AS asset_id,
        (
            date_trunc('month', gs)
            + interval '1 month'
            - interval '1 day'
        )::date AS depreciation_date
    FROM asset_base ab
    CROSS JOIN generate_series(
        ab.date_comptabilisation,
        ab.end_date,
        interval '1 month'
    ) gs
),

real_lines AS (
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
),

estimated_base AS (
    SELECT
        s.asset_id,
        s.depreciation_date,
        ab.*,
        (
            ab.daily_amount *
            (
                s.depreciation_date
                - date_trunc('month', s.depreciation_date)::date
                + 1
            )
        ) AS base_amount
    FROM schedule s
    JOIN asset_base ab ON ab.id = s.asset_id
),

estimated_cum AS (
    SELECT
        eb.*,
        SUM(eb.base_amount) OVER (
            PARTITION BY eb.id
            ORDER BY eb.depreciation_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS cum_before
    FROM estimated_base eb
)

SELECT
    -- IDENTIFICATION ----------------------------------------------------------
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

    compte_depreciation.code || ' ' || compte_depreciation.name
        || ' (' || compte_depreciation_company.name || ')'
        AS "Compte de dépréciation",

    compte_expense_depreciation.code || ' ' || compte_expense_depreciation.name
        || ' (' || compte_expense_depreciation_company.name || ')'
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

    aaat.old_id                 AS "Ancien ID",

    -- DATE --------------------------------------------------------------------
    ec.depreciation_date        AS "Date de dépréciation",
    rl.name                     AS "Nom amortissement",
    rl.type                     AS "Type",

    -- RÉEL --------------------------------------------------------------------
    rl.depreciated_value        AS "Montant déjà amorti réel",
    rl.amount                   AS "Amortissement courant réel",
    rl.remaining_value          AS "Période suivante réelle",
    rl.move_check               AS "Comptabilisé",

    -- ESTIMÉ ------------------------------------------------------------------
    CASE
        WHEN ec.depreciation_date < ec.end_date
            THEN ec.base_amount
        ELSE ec.purchase_value - COALESCE(ec.cum_before, 0)
    END AS "Amortissement courant estimé",

    SUM(
        CASE
            WHEN ec.depreciation_date < ec.end_date
                THEN ec.base_amount
            ELSE ec.purchase_value - COALESCE(ec.cum_before, 0)
        END
    ) OVER (
        PARTITION BY ec.id
        ORDER BY ec.depreciation_date
    ) AS "Montant déjà amorti estimé",

    GREATEST(
        0,
        ec.purchase_value -
        SUM(
            CASE
                WHEN ec.depreciation_date < ec.end_date
                    THEN ec.base_amount
                ELSE ec.purchase_value - COALESCE(ec.cum_before, 0)
            END
        ) OVER (
            PARTITION BY ec.id
            ORDER BY ec.depreciation_date
        )
    ) AS "Période suivante estimée"

FROM estimated_cum ec
JOIN account_asset_asset aaat ON aaat.id = ec.id

LEFT JOIN real_lines rl
    ON rl.asset_id = ec.id
    AND rl.depreciation_date = ec.depreciation_date

LEFT JOIN account_asset_category aac
    ON aaat.category_id = aac.id
LEFT JOIN gmao_equipment_equipment gee
    ON aaat.equipement_id = gee.id
LEFT JOIN fleet_vehicle fv
    ON aaat.vehicle_id = fv.id
LEFT JOIN account_asset_affectation aaaf
    ON aaat.affectation_id = aaaf.id
LEFT JOIN hr_employee
    ON aaat.employee_affected_id = hr_employee.id
LEFT JOIN res_currency
    ON aaat.currency_id = res_currency.id

LEFT JOIN res_company societe_comptable
    ON societe_comptable.id = aaat.company_id
LEFT JOIN asset_center_cout acck
    ON acck.id = aaat.center_cout_id
LEFT JOIN res_company rc_cout
    ON acck.company_id = rc_cout.id

LEFT JOIN account_account compte_immo
    ON compte_immo.id = aaat.account_asset_id
LEFT JOIN res_company compte_immo_company
    ON compte_immo_company.id = compte_immo.company_id

LEFT JOIN account_account compte_depreciation
    ON compte_depreciation.id = aaat.account_depreciation_id
LEFT JOIN res_company compte_depreciation_company
    ON compte_depreciation_company.id = compte_depreciation.company_id

LEFT JOIN account_account compte_expense_depreciation
    ON compte_expense_depreciation.id = aaat.account_expense_depreciation_id
LEFT JOIN res_company compte_expense_depreciation_company
    ON compte_expense_depreciation_company.id = compte_expense_depreciation.company_id

ORDER BY ec.depreciation_date
"""

    return sql, asset_filter_param
