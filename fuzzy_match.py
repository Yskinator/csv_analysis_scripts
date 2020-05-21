import sys
import csv
from fuzzywuzzy import process

csv.field_size_limit(int(sys.maxsize/100000000000))

if __name__ == "__main__":
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
            commodities.append(commodity)
            segments.append(segment)
    print("Extracting...")
    with open('stock_sample.csv', encoding="UTF-8") as f:
        r = csv.reader(f)
        for i, row in enumerate(r):
            descr = row[3].split(";")[0]
            result = process.extractOne(descr, commodities)
            result_segment = segments[commodities.index(result[0])]
            print(descr+" -> "+str(result_segment))
            if i > 10:
                break
    print("Finished.")