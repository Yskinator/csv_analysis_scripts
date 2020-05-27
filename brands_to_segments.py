"""Connect brands to their most likely product segments."""

import csv
import spacy
from embedding_match import extract, load_segments
from file_utils import read_csv

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

def match_brands_segments(nlp, brands, brand_counts, commodities, segments):
    """Match brands to most probable segments."""
    keys = ['Brand', 'Count', 'Segment Name']
    brands_to_seg = []
    for i, brand in enumerate(brands.keys()):
        # Run embedding matching on descriptions
        possible_segments = []
        for descr in brands[brand]:
            descr_doc = nlp(descr)
            if descr_doc.has_vector and descr_doc.vector_norm != 0:
                results = extract(descr_doc, commodities, 1)
                possible_segments.append(segments[results[0][0]])
        segment = max(possible_segments, key=possible_segments.count)
        count = brand_counts[brand] if brand in brand_counts else 0
        brands_to_seg.append(dict(zip(keys, [brand, count, '"'+segment+'"'])))
        if i%100 == 0:
            print(i, (brand, segment))
    return brands_to_seg

def save_segments(brands_to_seg, filename):
    """Save brands_to_segments mapping to a csv file."""
    print("Writing to file...")
    with open(filename, encoding="UTF-8", mode="w+") as csv_file:
        csv_file.write("\n".join([",".join(row) for row in brands_to_seg]))
    print("Finished.")

def brands_to_segments(segment_strings, brand_counts, preprocessed):
    """Map brands in preprocessed to segments defined in segment_strings.
        Ignore cases where brand_count < 20."""
    print("Loading brands...")
    brands = process_brands(preprocessed, brand_counts)
    print("Loading spacy vectors...")
    nlp = spacy.load("en_vectors_web_lg")
    nlp.max_length = 1006000
    print("Loading segments...")
    commodities, segments = load_segments(segment_strings, nlp)
    print("Matching brands to segments...")
    brands_to_seg = match_brands_segments(nlp, brands, brand_counts, commodities, segments)
    return brands_to_seg

if __name__ == "__main__":
    SEGMENT_STRINGS = read_csv("segment_strings.csv")
    BRAND_COUNTS = read_csv("brand_counts.csv")
    PREPROCESSED = read_csv("preprocessed.csv")
    BRANDS_TO_SEG = brands_to_segments(SEGMENT_STRINGS, BRAND_COUNTS, PREPROCESSED)
    save_segments(BRANDS_TO_SEG, "brands_to_segments.csv")
