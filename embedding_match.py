import sys
import os
import csv
import spacy

csv.field_size_limit(int(sys.maxsize/100000000000))

def load_segments(rows, nlp):
    """Load segments from file segments_file."""
    excluded = excluded_segments()
    commodities = []
    segments = []
    for row in rows:
        if row["Segment Name"] in excluded:
            continue
        #commodity = row['Commodity Name']
        commodity = row['Segment String']
        segment = row['Segment Name']
        commodities.append(nlp(commodity))
        segments.append(segment)
    return (commodities, segments)

def excluded_segments():
    exs = []
    with open("excluded_segments.csv") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["Remove?"] == "YES" or row["Remove?"] == "YES?":
                exs.append(row["Segment Name"])
    return exs

def load_brand_segments(rows):
    """Load segments associated with a file."""
    brand_seg = {}
    for row in rows:
        brand_seg[row['Brand']] = row['Segment Name']
    return brand_seg

def extract(text, choices, num):
    ordered_choices = []
    for i, choice in enumerate(choices):
        ordered_choices.append((i, choice.similarity(text)))
    ordered_choices = sorted(ordered_choices, key=lambda row: row[0], reverse=True)
    return ordered_choices[0:num]

def add_segments(preprocessed_rows, nlp, commodities, segments, brand_seg=None):
    """Read rows from supplied csv filepath, calculate and append segments string as new column."""
    new_rows = []
    for i, row in enumerate(preprocessed_rows):
        new_row = row.copy()
        descr = row["Description"]
        brand = row["Brands"]
        results = extract(nlp(descr), commodities, 20)
        result_segments = [(segments[i], prob) for i, prob in results]
        if brand_seg and brand in brand_seg.keys():
            segment = brand_seg[brand]
            if not segment in result_segments:
                result_segments = [(segment, 1.0)]+result_segments
                print("Row "+str(i)+": Added segment "+segment+" to "+descr+" based on brand.")
        new_row["Segments"] = ";".join([r[0] for r in result_segments])
        new_rows.append(new_row)
    return new_rows

def csv_write(filepath, rows):
    print("Writing to file...")
    with open(filepath, encoding="UTF-8", mode="w+", newline='') as sample_file:
        writer = csv.writer(sample_file)
        for row in rows:
            writer.writerow(row)
    print("Finished.")

def embedding_match(segment_strings, brands_segments, preprocessed_stocks):
    print("Loading spacy vectors...")
    nlp = spacy.load("en_vectors_web_lg")
    nlp.max_length = 1006000
    print("Reading commodity types...")
    commodities, segments = load_segments(segment_strings, nlp)
    print("Loading brand segments...")
    brand_seg = load_brand_segments(brands_segments)
    print("Extracting...")
    new_rows = add_segments(preprocessed_stocks, nlp, commodities, segments, brand_seg)
    return new_rows

if __name__ == "__main__":
    embedding_match()
