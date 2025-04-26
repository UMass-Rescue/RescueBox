import os
import numpy as np
from pathlib import Path
import logging
import pandas as pd
from src.utils.sqlAlchemy_manager import DBManager
from src.utils.preprocess import is_valid_image, is_damaged

logging.basicConfig(level=logging.INFO)

def read_csv_and_format(fileIn: str="age_gender.csv") -> pd.DataFrame:
    "Read labeled data set and return DataFrame"
    path = Path(__file__).parent
    file = str(path / fileIn)
    if not os.path.exists(file):
        raise FileNotFoundError(f" File not found: {file}")
    return pd.read_csv(file)


def transform_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    # cleaning pixels column for image preprocessing
    df = df[df["pixels"].apply(is_valid_image)].copy()
    df["pixels_array"] = df["pixels"].apply(lambda x: np.array([int(p) for p in x.split()], dtype=np.uint8).reshape(48, 48))
    df = df[~df["pixels_array"].apply(is_damaged)]
    df = df.drop(columns=["pixels_array"])
    logging.info(" Completed raw pixel transformations")
    return df


def clean_load_to_db(df: pd.DataFrame, table_name: str="age_gender_labeled") -> None:
    """Connect to DB, create/truncate table, write df to table."""
    db_uri = os.getenv("DB_CONN_STR")
    db = DBManager(db_uri, table_name)

    db.create_table_if_not_exists()
    db.truncate_table()

    df.to_sql(table_name, con=db.engine, if_exists="append", index=False)
    ct = pd.read_sql(f"SELECT COUNT(*) FROM {table_name}", con=db.engine).iloc[0, 0]
    logging.info(f" Clean loaded {ct} records into DB table {table_name}")


def main() -> None:
    df = read_csv_and_format()
    df = transform_raw_data(df)
    clean_load_to_db(df)


if __name__ == "__main__":
    main()