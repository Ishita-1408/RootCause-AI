"""RootCause AI - Reusable EDA & Analysis Helper Utilities.

Provides clean wrappers for querying Supabase PostgreSQL, converting query results
into pandas DataFrames with strict type casting, formatting currency/percentages,
and supporting reproducible exploratory data analysis.
"""

from typing import Any

import pandas as pd
import psycopg
from psycopg.rows import dict_row

from apps.api.config import get_settings


def get_db_conn() -> psycopg.Connection:
    """Create and return a psycopg database connection using environment config."""
    settings = get_settings()
    return psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=settings.database_password,
        connect_timeout=15,
    )


def query_df(query: str, params: tuple[Any, ...] | None = None) -> pd.DataFrame:
    """Execute a parameterized SQL query and return results as a pandas DataFrame."""
    with get_db_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([dict(row) for row in rows])


def format_currency_brl(val: float | int | None) -> str:
    """Format a numeric value as Brazilian Real currency (R$ X,XXX.XX)."""
    if val is None or pd.isna(val):
        return "R$ 0.00"
    return f"R$ {float(val):,.2f}"


def format_pct(val: float | int | None, decimals: int = 1) -> str:
    """Format a numeric value as a percentage string (XX.X%)."""
    if val is None or pd.isna(val):
        return "0.0%"
    return f"{float(val):.{decimals}f}%"


# -----------------------------------------------------------------------------
# Core Analytical Calculation Formulas (Unit-Testable without Live Database)
# -----------------------------------------------------------------------------


def calculate_aov(total_revenue: float, total_orders: int) -> float:
    """Calculate Average Order Value (AOV) safely preventing division by zero."""
    if total_orders <= 0:
        return 0.0
    return total_revenue / total_orders


def calculate_rate_pct(numerator: int | float, denominator: int | float) -> float:
    """Calculate rate percentage safely preventing division by zero."""
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0


def calculate_repeat_rate(total_customers: int, repeat_customers: int) -> float:
    """Calculate repeat customer percentage."""
    return calculate_rate_pct(repeat_customers, total_customers)
