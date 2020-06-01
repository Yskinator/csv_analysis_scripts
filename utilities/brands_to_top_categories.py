"""Connect brands to their most likely product top_categories."""

import csv
import spacy
from .embedding_match import extract, load_top_categories
from .file_utils import read_csv

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
    nlp = spacy.load("en_vectors_web_lg")
    nlp.max_length = 1006000
    print("Loading top_categories...")
    commodities, top_categories = load_top_categories(top_category_strings, nlp)
    print("Matching brands to top_categories...")
    brands_to_tc = match_brands_top_categories(nlp, brands, brand_counts, commodities, top_categories)
    return brands_to_tc

if __name__ == "__main__":
    TOP_CATEGORY_STRINGS = read_csv("top_category_strings.csv")
    BRAND_COUNTS = read_csv("brand_counts.csv")
    PREPROCESSED = read_csv("preprocessed.csv")
    BRANDS_TO_SEG = brands_to_top_categories(TOP_CATEGORY_STRINGS, BRAND_COUNTS, PREPROCESSED)
    save_top_categories(BRANDS_TO_SEG, "brands_to_top_categories.csv")
