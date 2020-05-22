import sys
import os
import csv
import spacy

csv.field_size_limit(int(sys.maxsize/100000000000))

def load_segments(segments_file, nlp):
    """Load segments from file segments_file."""
    with open(segments_file) as f:
        r = csv.DictReader(f)
        commodities = []
        segments = []
        for row in r:
            #commodity = row['Commodity Name']
            commodity = row['Segment String']
            segment = row['Segment Name']
            commodities.append(nlp(commodity))
            segments.append(segment)
    return (commodities, segments)

def load_brand_segments(filepath):
    """Load segments associated with a file."""
    with open(filepath, encoding="UTF-8") as f:
        r = csv.DictReader(f)
        brand_seg = {}
        for row in r:
            brand_seg[row['Brand']] = row['Segment Name']
    return brand_seg

def extract(text, choices, num):
    ordered_choices = []
    for i, choice in enumerate(choices):
        ordered_choices.append((i, choice.similarity(text)))
    ordered_choices = sorted(ordered_choices, key=lambda row: row[1], reverse=True)
    return ordered_choices[0:num]

def add_segments(filepath, nlp, commodities, segments, brand_seg=None):
    """Read rows from supplied csv filepath, calculate and append segments string as new column."""
    with open(filepath, encoding="UTF-8") as f:
        r = csv.reader(f)
        new_rows = []
        for i, row in enumerate(r):
            new_row = row.copy()
            descr = row[0]
            brand = row[2]
            results = extract(nlp(descr), commodities, 15)
            result_segments = [(segments[i], prob) for i, prob in results]
            if brand_seg and brand in brand_seg.keys():
                segment = brand_seg[brand]
                if not segment in result_segments:
                    result_segments = [(segment, 1.0)]+result_segments
                    print("Row "+str(i)+": Added segment "+segment+" to "+descr+" based on brand.")
            if i%250 == 0:
                print(descr+" -> "+str(result_segments))
            new_rows.append(new_row+[";".join([r[0] for r in result_segments])])
        new_rows[0][3] = "Segments" # Fix the fourth column of header prior to writing to file
    return new_rows

def csv_write(filepath, rows):
    with open(filepath, encoding="UTF-8", mode="w+", newline='') as sample_file:
        writer = csv.writer(sample_file)
        for row in rows:
            writer.writerow(row)

def embedding_match():
    if os.path.isfile("stock_with_segments.csv"):
        return
    print("Loading spacy vectors...")
    nlp = spacy.load("en_vectors_web_lg")
    nlp.max_length = 1006000
    print("Reading commodity types...")
    commodities, segments = load_segments('segment_strings.csv', nlp)
    print("Loading brand segments...")
    brand_seg = load_brand_segments("brands_to_segments.csv")
    print("Extracting...")
    new_rows = add_segments('preprocessed_stocks_with_brands.csv', nlp, commodities, segments, brand_seg)
    print("Writing to file...")
    csv_write('stock_with_segments.csv', new_rows)
    print("Finished.")

if __name__ == "__main__":
    embedding_match()
