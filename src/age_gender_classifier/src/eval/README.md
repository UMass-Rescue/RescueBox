## Evaluating Labeled Data Set

**Pre-requisite**  
Ensure the labeled data set exists in the data store. If not, follow steps in the `init_data` directory.  

**Analyze Model Efficacy**
- Analyze raw labeled data set: `analyze_labeled_data_raw.py` writes charts for age distribution and gender counts to `imgs/` directory.  
- Score labeled data: `score_labeled_data.py` runs labeled data through our models and writes scores to the DB.  
- Analyze scored labeled data: `analyze_labeled_data_scored.py` visualize model efficacy and writes charts to `imgs/` directory.  

Process is grouped in `eval_main.py`

    poetry run python src/eval/eval_main.py
