import pandas as pd
from src.eval.analyze_labeled_data_raw import main as raw_main
from src.eval.score_labeled_data import main as run_evaluation
from eval.transform_scores import main as transform_outputs


def main(
    eval_table: str = "age_gender_labeled", raw_plots: bool = False
) -> pd.DataFrame:
    """Orchestrate full evaluation pipeline.

    - Plot raw data, if raw_plots is True
    - Run eval, query true samples and run Survey models
    - Transform outputs, extract predictions from json payload
    - Plot predicted data
    """
    if raw_plots:
        raw_main(eval_table)

    ts, df = run_evaluation()

    df = transform_outputs(t_stamp=ts)

    # TODO: endpoint for visualizations here
    # chart scores and true/predicted labels

    return df


if __name__ == "__main__":
    main()
