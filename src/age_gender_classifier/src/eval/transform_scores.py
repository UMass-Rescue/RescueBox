from pathlib import Path
import logging
import json
import pandas as pd
from typing import Optional

from src.utils.common import read_db

logging.basicConfig(level=logging.INFO)
path = Path(__file__).parent


def flatten_json_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Expand json scores from model_output."""
    scores_expanded = pd.json_normalize(df["scores"].apply(lambda x: json.loads(x)))
    df = df.join(scores_expanded).drop("scores", axis=1)
    logging.info(" Expanded JSON scores")
    return df


def main(t_stamp: Optional[str] = None) -> pd.DataFrame:
    """Read values from DB where created_at = t_stamp,
    expand json scores into separate columns, and return a dataframe.
    """
    if t_stamp is None:
        df = pd.read_csv(path / "temp_output.csv", header=0, index_col=False)
    else:
        pred_df = read_db(
            table_name="model_output",
            query=f"SELECT * FROM model_output where created_at = '{t_stamp}' order by created_at",
        )
        df = flatten_json_scores(pred_df)
        df.to_csv(path / "temp_output.csv", index=False)

    true_df = read_db(
        table_name="age_gender_labeled",
        query="SELECT age AS true_label, img_name FROM age_gender_labeled",
    )

    df_merged = pd.merge(df, true_df, left_on="imageId", right_on="img_name").drop(
        "img_name", axis=1
    )
    df_merged.to_csv(path / "temp_output_labeled.csv", index=False)

    return df_merged


if __name__ == "__main__":
    main()
