### How to get the evaluation data set

The evaluation dataset is 199MB in size, too large to check into GitHub.  
Download it from [here](https://www.kaggle.com/datasets/nipunarora8/age-gender-and-ethnicity-face-data-csv/data), and save the file in this directory as `age_gender.csv`.  

### Load into SQLite

Run the `load_db.py` file. This reads the downloaded CSV file, connects to the database, creates a new table if it does not exist, truncates the table, and writes the data.

    poetry run python src/init_data/load_db.py
