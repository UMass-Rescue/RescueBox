from pathlib import Path
import logging
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from src.utils.common import read_db

logging.basicConfig(level=logging.INFO)
path = Path(__file__).parent


def age_histogram(
    df: pd.DataFrame, saveFile: str = "imgs/age_distribution.png"
) -> None:
    """"""
    sns.histplot(data=df, x="age", kde=True)
    plt.savefig(path / saveFile)
    logging.info(f" Saved histogram to {saveFile}")


def gender_counts(df: pd.DataFrame, saveFile: str = "imgs/gender_counts.png") -> None:
    """"""
    gender_counts = {0: (df["gender"] == 0).sum(), 1: (df["gender"] == 1).sum()}
    sns.barplot(
        x=["Male", "Female"],
        y=[gender_counts[0], gender_counts[1]],
        palette=["gray", "orange"],
        hue=["Male", "Female"],
        width=0.5,
    )
    plt.ylabel("Count")
    plt.savefig(path / saveFile)
    logging.info(f" Saved histogram to {saveFile}")


def main(table: str = "age_gender_labeled"):
    """Labeled data set must exist in the database."""
    df = read_db(table_name=table, query=f"SELECT * FROM {table}")
    age_histogram(df)
    gender_counts(df)


if __name__ == "__main__":
    main()
