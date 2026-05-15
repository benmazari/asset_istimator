import yaml
import psycopg2
import psycopg2.extras

with open(r"c:\Users\benmazari_s\Desktop\amortissement\config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

conn = psycopg2.connect(
    host=cfg["database"]["host"],
    port=cfg["database"]["port"],
    dbname=cfg["database"]["dbname"],
    user=cfg["database"]["user"],
    password=cfg["database"]["password"]
)

sql = """
WITH asset_base AS (
    SELECT
        aaat.*,

        --------------------------------------------------
        -- 🔥 DURATION FROM EXCEL
        --------------------------------------------------
        CASE 
            WHEN aaat.category_id = 1 THEN 20
            WHEN aaat.category_id = 2 THEN 30
            WHEN aaat.category_id = 3 THEN 30
            WHEN aaat.category_id = 4 THEN 20
            WHEN aaat.category_id = 5 THEN 20
            WHEN aaat.category_id = 9 THEN 4
            WHEN aaat.category_id = 13 THEN 10
            WHEN aaat.category_id = 16 THEN 5
            WHEN aaat.category_id = 18 THEN 10
            WHEN aaat.category_id = 20 THEN 10
            WHEN aaat.category_id = 21 THEN 5
            WHEN aaat.category_id = 24 THEN 3
            WHEN aaat.category_id = 25 THEN 5
            WHEN aaat.category_id = 29 THEN 7
            ELSE NULL
        END AS duration_years,

        --------------------------------------------------
        -- 🔥 END DATE
        --------------------------------------------------
        (
            aaat.date_comptabilisation 
            + (
                interval '1 year' * 
                CASE 
                    WHEN aaat.category_id = 1 THEN 20
                    WHEN aaat.category_id = 2 THEN 30
                    WHEN aaat.category_id = 3 THEN 30
                    WHEN aaat.category_id = 4 THEN 20
                    WHEN aaat.category_id = 5 THEN 20
                    WHEN aaat.category_id = 9 THEN 4
                    WHEN aaat.category_id = 13 THEN 10
                    WHEN aaat.category_id = 16 THEN 5
                    WHEN aaat.category_id = 18 THEN 10
                    WHEN aaat.category_id = 20 THEN 10
                    WHEN aaat.category_id = 21 THEN 5
                    WHEN aaat.category_id = 24 THEN 3
                    WHEN aaat.category_id = 25 THEN 5
                    WHEN aaat.category_id = 29 THEN 7
                    ELSE NULL
                END
            )
            - interval '1 day'
        )::date AS end_date,

        --------------------------------------------------
        -- 🔥 DAILY AMOUNT (365 DAYS FIXED)
        --------------------------------------------------
        CASE 
            WHEN 
                CASE 
                    WHEN aaat.category_id = 1 THEN 20
                    WHEN aaat.category_id = 2 THEN 30
                    WHEN aaat.category_id = 3 THEN 30
                    WHEN aaat.category_id = 4 THEN 20
                    WHEN aaat.category_id = 5 THEN 20
                    WHEN aaat.category_id = 9 THEN 4
                    WHEN aaat.category_id = 13 THEN 10
                    WHEN aaat.category_id = 16 THEN 5
                    WHEN aaat.category_id = 18 THEN 10
                    WHEN aaat.category_id = 20 THEN 10
                    WHEN aaat.category_id = 21 THEN 5
                    WHEN aaat.category_id = 24 THEN 3
                    WHEN aaat.category_id = 25 THEN 5
                    WHEN aaat.category_id = 29 THEN 7
                    ELSE NULL
                END IS NULL
            THEN NULL

            ELSE 
                aaat.purchase_value /
                (
                    (
                        CASE 
                            WHEN aaat.category_id = 1 THEN 20
                            WHEN aaat.category_id = 2 THEN 30
                            WHEN aaat.category_id = 3 THEN 30
                            WHEN aaat.category_id = 4 THEN 20
                            WHEN aaat.category_id = 5 THEN 20
                            WHEN aaat.category_id = 9 THEN 4
                            WHEN aaat.category_id = 13 THEN 10
                            WHEN aaat.category_id = 16 THEN 5
                            WHEN aaat.category_id = 18 THEN 10
                            WHEN aaat.category_id = 20 THEN 10
                            WHEN aaat.category_id = 21 THEN 5
                            WHEN aaat.category_id = 24 THEN 3
                            WHEN aaat.category_id = 25 THEN 5
                            WHEN aaat.category_id = 29 THEN 7
                            ELSE NULL
                        END
                    ) * 365
                )::numeric

        END AS daily_amount

    FROM account_asset_asset aaat
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
        date_trunc('month', ab.date_comptabilisation)::date,
        date_trunc('month', ab.end_date)::date,
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

        CASE 
            WHEN ab.daily_amount IS NULL THEN NULL

            ELSE
                ab.daily_amount *
                (
                    CASE

                        --------------------------------------------------
                        -- 🔥 FIRST MONTH
                        --------------------------------------------------
                        WHEN date_trunc('month', s.depreciation_date)
                             =
                             date_trunc('month', ab.date_comptabilisation)

                        THEN
                            s.depreciation_date
                            - ab.date_comptabilisation
                            + 1

                        --------------------------------------------------
                        -- 🔥 LAST MONTH
                        --------------------------------------------------
                        WHEN date_trunc('month', s.depreciation_date)
                             =
                             date_trunc('month', ab.end_date)

                        THEN
                            ab.end_date
                            - date_trunc('month', ab.end_date)::date
                            + 1

                        --------------------------------------------------
                        -- 🔥 FULL MONTHS
                        --------------------------------------------------
                        ELSE
                            s.depreciation_date
                            - date_trunc('month', s.depreciation_date)::date
                            + 1

                    END
                )

        END AS base_amount

    FROM schedule s
    JOIN asset_base ab 
        ON ab.id = s.asset_id
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

SELECT DISTINCT
    aac.id AS id_categ,
    aac.name AS categ
FROM estimated_cum ec
JOIN account_asset_asset aaat ON aaat.id = ec.id
LEFT JOIN account_asset_category aac ON aac.id = aaat.category_id
LEFT JOIN res_company societe_comptable ON societe_comptable.id = aaat.company_id
WHERE date_part ('year',aaat.date_comptabilisation) = '2025'
AND aaat.company_location_id = 20;
"""

with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    cur.execute(sql)
    rows = cur.fetchall()
    print("--- CATEGORIES RETURNED BY USER'S EXACT REFERENCE QUERY ---")
    for r in rows:
        print(f"ID: {r['id_categ']}, Name: {r['categ']}")

conn.close()
