"""
db.py — PostgreSQL connection and query execution.
Returns results as a pandas DataFrame.
"""

import psycopg2
import psycopg2.extras
import pandas as pd


def get_connection(db_cfg: dict):
    """Create and return a psycopg2 connection from the config dict."""
    # statement_timeout: max time (ms) any single SQL query can run
    # connect_timeout:   max seconds to wait for initial connection
    statement_timeout_ms = db_cfg.get("statement_timeout_ms", 300_000)  # 5 min default
    return psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg.get("port", 5432),
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        connect_timeout=db_cfg.get("connect_timeout", 15),
        options=f"-c statement_timeout={statement_timeout_ms}",
    )


def run_query(conn, sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Execute a SQL query and return the results as a DataFrame.

    Args:
        conn:   An open psycopg2 connection.
        sql:    The SQL query string (may contain %s placeholders).
        params: Tuple of parameters matching %s placeholders.

    Returns:
        pandas DataFrame with column names from the cursor description.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
    return pd.DataFrame(rows, columns=columns)
