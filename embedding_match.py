import sys
import csv
import spacy

csv.field_size_limit(int(sys.maxsize/100000000000))

def extract(text, choices, num):
    ordered_choices = []
    for i, choice in enumerate(choices):
        ordered_choices.append((i, choice.similarity(text)))
    ordered_choices = sorted(ordered_choices, key=lambda row: row[1], reverse=True)
    return ordered_choices[0:num]

if __name__ == "__main__":
    print("Loading spacy vectors...")
    nlp = spacy.load("en_vectors_web_lg")
    nlp.max_length = 1006000
    print("Reading commodity types...")
    #with open('unspsc_codes_3.csv') as f:
    with open('segment_strings.csv') as f:
        r = csv.DictReader(f)
        commodities = []
        segments = []
        for row in r:
            #commodity = row['Commodity Name']
            commodity = row['Segment String']
            segment = row['Segment Name']
            commodities.append(nlp(commodity))
            segments.append(segment)
    print("Extracting...")
    with open('stock_sample_preprocessed.csv', encoding="UTF-8") as f:
        r = csv.reader(f)
        new_rows = []
        for i, row in enumerate(r):
            new_row = row.copy()
            descr = row[0]#.split(";")[0]
            results = extract(nlp(descr), commodities, 3)
            #result_segment = segments[result_index]
            result_segments = [(segments[i], prob) for i, prob in results]
            if i%10 == 0:
                print(descr+" -> "+str(result_segments))
            new_rows.append(new_row+[";".join([r[0] for r in result_segments])])
    with open('stock_sample_with_segments.csv', mode="w+") as sample_file:
        sample_file.write("\n".join([",".join(row) for row in new_rows]))
    print("Finished.")
