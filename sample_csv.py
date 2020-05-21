import csv
import random

CSV_PATH = "preprocessed_stocks.csv"
CSV_LENGTH = 160786
SAMPLE_NUM = 1000

if __name__ == "__main__":
    with open(CSV_PATH, encoding="UTF-8") as csvfile:
        reader = csv.reader(csvfile)
        sample_indices = random.sample(range(1, CSV_LENGTH), k=SAMPLE_NUM)
        sample_indices = [0]+sample_indices # Add CSV header row to indices
        rows = []
        for i, row in enumerate(reader):
            if i in sample_indices:
                rows.append(row)
    with open('stock_sample_preprocessed.csv', "w+") as sample_file:
        sample_file.write("\n".join([",".join(row) for row in rows]))
    print("Finished.")
