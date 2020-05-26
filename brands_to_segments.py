"""Connect brands to their most likely product segments."""

import os
import csv
import spacy
from embedding_match import extract, load_segments

def load_brands(filepath, brand_counts):
    """Load brands from csv specified by filepath, while ignoring brands with a brandcount < 20."""
    with open(filepath, encoding="UTF-8") as f:
        r = csv.DictReader(f)
        brands = {}
        for row in r:
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

def process_brands(preprocessed, brand_counts):
    """Process brands from list of dictionaries specified by preprocessed, while ignoring brands with a brandcount < 20."""
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
    brands_to_segments = [['Brand', 'Count', 'Segment Name']]
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
        brands_to_segments.append([brand, count, '"'+segment+'"'])
        if i%100 == 0:
            print(i, (brand, segment))
    return brands_to_segments

def save_segments(brands_to_segments, filename):
    print("Writing to file...")
    with open(filename, encoding="UTF-8", mode="w+") as f:
        f.write("\n".join([",".join(r) for r in brands_to_segments]))
    print("Finished.")

def brands_to_segments(segment_strings, brand_counts, preprocessed):
    print("Loading brands...")
    brands = process_brands(preprocessed, brand_counts)
    print("Loading spacy vectors...")
    nlp = spacy.load("en_vectors_web_lg")
    nlp.max_length = 1006000
    print("Loading segments...")
    commodities, segments = load_segments(segment_strings, nlp)
    print("Matching brands to segments...")
    brands_to_segments = match_brands_segments(nlp, brands, brand_counts, commodities, segments)
    return brands_to_segments

if __name__ == "__main__":
    brands_to_segments()
