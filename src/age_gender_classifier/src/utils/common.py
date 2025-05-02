import os
from typing import Optional
import logging
import pandas as pd
from src.utils.sqlAlchemy_manager import DBManager

logging.basicConfig(level=logging.INFO)
db_uri = os.getenv("DB_CONN_STR")


def read_db(
    table_name: str = "age_gender_labeled", query: Optional[str] = None
) -> pd.DataFrame:
    """Read records from custom query into pandas DataFrame."""
    if query is None:
        logging.warning("No query provided. Returning None.")
        return None

    db = DBManager(db_uri, table_name)
    df = pd.read_sql(query, con=db.engine)
    logging.info(f" Retrieved {len(df)} records from DB table {table_name}")
    return df


def write_db(df: pd.DataFrame, table_name: str = "model_output") -> None:
    """Write pandas DataFrame of model output into DB."""

    db = DBManager(db_uri, table_name)
    db.create_table_if_not_exists()
    df.to_sql(table_name, con=db.engine, if_exists="append", index=False)
    logging.info(f" Wrote {len(df)} records to DB table {table_name}")
