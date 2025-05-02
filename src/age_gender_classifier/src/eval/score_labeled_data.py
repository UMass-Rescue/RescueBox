from pathlib import Path
from typing import Tuple
import logging
import pandas as pd

from src.utils.common import read_db
from src.onnx_models.survey_models import SurveyModels

logging.basicConfig(level=logging.INFO)
path = Path(__file__).parent


def main(
    table: str = "age_gender_labeled", mod_size: int = 200
) -> Tuple[str, pd.DataFrame]:
    """Read subset of true data from database, preprocess, run inference against our models,
    and return a dataframe. Labeled data set must exist in the database.

    Return: tuple of timestamp as str and dataframe
    """
    df = read_db(
        table_name=table,
        query=f"SELECT id, age, img_name, pixels FROM {table} where id % {mod_size} = 0 order by age",
    )

    imgs = list(df["pixels"])
    ids = list(df["img_name"])
    logging.info(
        f" About to run inference on true label subset of size = {len(df)} ..."
    )

    sm = SurveyModels()
    df = sm.main_predict_eval(imgs, age_threshold=20, ids=ids)

    logging.info(
        " Completed prediction on true labels, returning timestamp and dataframe of predicted results"
    )
    return sm.now, df


if __name__ == "__main__":
    main()
