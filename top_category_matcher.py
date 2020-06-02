"""Connect brands and rows to their most likely product top_categories."""
import sys
import os
import csv
import spacy
# if "LOCAL" in os.environ:
import file_utils
# else:
    # from . import file_utils

csv.field_size_limit(int(sys.maxsize/100000000000))


def load_brands(filepath, brand_counts):
    """Load brands from csv specified by filepath, ignoring brands with a brandcount < 20."""
    preprocessed = []
    with open(filepath, encoding="UTF-8") as brand_file:
        reader = csv.DictReader(brand_file)
        for row in reader:
            preprocessed.append(row)
    brands = process_brands(preprocessed, brand_counts)
    return brands

def process_brands(preprocessed, brand_counts):
    """Process brands from list of dicts 'preprocessed', ignoring brands with brandcount < 20."""
    brands = {}
    for row in preprocessed:
        brand_str = row['Brands']
        descr = row['Description']
        for brand in set(brand_str.split(";")):
            if not brand:
                continue
            if brand in brand_counts and int(brand_counts[brand]) < 20:
                # Ignore small brands, the results would not be reliable
                continue
            if brand in brands:
                brands[brand].append(descr)
            else:
                brands[brand] = [descr]
    return brands

def match_brands_top_categories(nlp, brands, brand_counts, commodities, top_categories):
    """Match brands to most probable top_categories."""
    keys = ['Brand', 'Count', 'Top Category Name']
    brands_to_tc = []
    for i, brand in enumerate(brands.keys()):
        # Run embedding matching on descriptions
        possible_top_categories = []
        for descr in brands[brand]:
            descr_doc = nlp(descr)
            if descr_doc.has_vector and descr_doc.vector_norm != 0:
                results = extract(descr_doc, commodities, 1)
                possible_top_categories.append(top_categories[results[0][0]])
        top_category = max(possible_top_categories, key=possible_top_categories.count)
        count = brand_counts[brand] if brand in brand_counts else 0
        brands_to_tc.append(dict(zip(keys, [brand, count, '"'+top_category+'"'])))
        if i%100 == 0:
            print(i, (brand, top_category))
    return brands_to_tc

def save_top_categories(brands_to_tc, filename):
    """Save brands_to_top_categories mapping to a csv file."""
    print("Writing to file...")
    with open(filename, encoding="UTF-8", mode="w+") as csv_file:
        csv_file.write("\n".join([",".join(row) for row in brands_to_tc]))
    print("Finished.")

def brands_to_top_categories(top_category_strings, brand_counts, preprocessed):
    """Map brands in preprocessed to top_categories defined in top_category_strings.
        Ignore cases where brand_count < 20."""
    print("Loading brands...")
    brands = process_brands(preprocessed, brand_counts)
    print("Loading spacy vectors...")
    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 1006000
    print("Loading top_categories...")
    commodities, top_categories = load_top_categories(top_category_strings, nlp)
    print("Matching brands to top_categories...")
    brands_to_tc = match_brands_top_categories(nlp, brands, brand_counts, commodities, top_categories)
    return brands_to_tc

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
    """If return_excluded is True, returns list of excluded top categories.
    If return_excluded is False, returns list of non-excluded top categories.
    This and excluded_segments should be renamed somehow."""
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
    nlp = spacy.load("en_core_web_sm")
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
    #TOP_CATEGORY_STRINGS = file_utils.read_csv("top_category_strings.csv")
    #BRAND_COUNTS = file_utils.read_csv("brand_counts.csv")
    #PREPROCESSED = file_utils.read_csv("preprocessed.csv")
    #BRANDS_TO_SEG = brands_to_top_categories(TOP_CATEGORY_STRINGS, BRAND_COUNTS, PREPROCESSED)
    #save_top_categories(BRANDS_TO_SEG, "brands_to_top_categories.csv")
