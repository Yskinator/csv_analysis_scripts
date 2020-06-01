import sys
import os
import csv
import spacy
# if "LOCAL" in os.environ:
import file_utils
# else:
    # from . import file_utils

csv.field_size_limit(int(sys.maxsize/100000000000))

def load_top_categories(rows, nlp):
    """Load top_categories from file top_categories_file."""
    excluded = excluded_top_categories()
    commodities = []
    top_categories = []
    for row in rows:
        if row["Top Category Name"] in excluded:
            continue
        #commodity = row['Commodity Name']
        commodity = row['Top Category String']
        top_category = row['Top Category Name']
        commodities.append(nlp(commodity))
        top_categories.append(top_category)
    return (commodities, top_categories)

def excluded_segments(return_excluded=True):
    exs = []
    rows = file_utils.read_csv("excluded_segments.csv")
    for row in rows:
        # print('row = ', row)
        if return_excluded:
            if row["Remove?"] == "YES" or row["Remove?"] == "YES?":
                exs.append(row["Segment Name"])
        if not return_excluded:
            if row["Remove?"] != "YES" or row["Remove?"] != "YES?":
                exs.append(row["Segment Name"])
    return exs

def excluded_top_categories(return_excluded=True):
    ex_segs = excluded_segments()
    tcs = file_utils.top_category_names()
    ex_tcs = []
    for tc in tcs:
        rows = file_utils.read_csv("top_category_files/" + tc +".csv")
        #There can never be more than one segment in a top category -> check first row
        if return_excluded:
            if rows[0]["Segment Name"] in ex_segs:
                ex_tcs.append(tc)
        else:
            if rows[0]["Segment Name"] not in ex_segs:
                ex_tcs.append(tc)
    return ex_tcs

def load_brand_top_categories(rows):
    """Load top_categories associated with a file."""
    brand_tc = {}
    for row in rows:
        brand_tc[row['Brand']] = row['Top Category Name']
    return brand_tc

def extract(text, choices, num):
    ordered_choices = []
    for i, choice in enumerate(choices):
        ordered_choices.append((i, choice.similarity(text)))
    ordered_choices = sorted(ordered_choices, key=lambda row: row[0], reverse=True)
    return ordered_choices[0:num]

def add_top_categories(preprocessed_rows, nlp, commodities, top_categories, tc_to_check_count, brand_tc=None):
    """Read rows from supplied csv filepath, calculate and append top_categories string as new column."""
    new_rows = []
    for i, row in enumerate(preprocessed_rows):
        new_row = row.copy()
        descr = row["Description"]
        brand = row["Brands"]
        results = extract(nlp(descr), commodities, tc_to_check_count)
        result_top_categories = [(top_categories[i], prob) for i, prob in results]
        if brand_tc and brand in brand_tc.keys():
            top_category = brand_tc[brand]
            if not top_category in result_top_categories:
                result_top_categories = [(top_category, 1.0)]+result_top_categories
                print("Row "+str(i)+": Added top_category "+top_category+" to "+descr+" based on brand.")
        new_row["Top Categories"] = ";".join([r[0] for r in result_top_categories])
        new_rows.append(new_row)
    return new_rows

def csv_write(filepath, rows):
    print("Writing to file...")
    with open(filepath, encoding="UTF-8", mode="w+", newline='') as sample_file:
        writer = csv.writer(sample_file)
        for row in rows:
            writer.writerow(row)
    print("Finished.")

def embedding_match(top_category_strings, brands_top_categories, preprocessed_stocks, tc_to_check_count = 100):
    print("Loading spacy vectors...")
    nlp = spacy.load("en_vectors_web_sm")
    nlp.max_length = 1006000
    print("Reading commodity types...")
    commodities, top_categories = load_top_categories(top_category_strings, nlp)
    print("Loading brand top_categories...")
    brand_tc = load_brand_top_categories(brands_top_categories)
    print("Extracting...")
    new_rows = add_top_categories(preprocessed_stocks, nlp, commodities, top_categories, tc_to_check_count, brand_tc)
    return new_rows

if __name__ == "__main__":
    embedding_match()
