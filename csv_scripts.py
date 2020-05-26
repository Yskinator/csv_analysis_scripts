import os
import sys
import csv
import re
import concurrent.futures
import brands_to_segments
import embedding_match
from file_utils import read_csv

csv.field_size_limit(int(sys.maxsize/100000000000))

#Note: Requires csv files generated by generate_segment_files to be in the segment_files/ folder
def match_commodities(stock_with_segments):
    rows = []
    brands = get_brands()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for row in stock_with_segments:
            futures.append(executor.submit(match_commodities_for_row, row, brands))
        for future in futures:
            updated_row = future.result()
            rows.append(updated_row)
    return rows

def match_commodities_for_row(row, brands = []):
    d = row["Description"]
    print("Row " + row["id"] + ", matching commodities.")
    seg_string = row["Segments"].replace('"', "")
    segs = filter(None, seg_string.split(";"))
    commodities = {}
    for s in segs:
        with open("segment_files/" + s + ".csv") as f2:
            r2 = csv.DictReader(f2)
            for row2 in r2:
                if row2["Commodity Name"] in commodities:
                    print("Duplicate commodity: " + row2["Commodity Name"])
                commodities[row2["Commodity Name"]] = row2["Commodity"]
    #results = process.extract(d, list(commodities), limit=3)
    results = most_matching_words(d, list(commodities), limit=1, brands = brands)
    r_string = ""
    commodity_codes = ""
    if len(results) == 1:
        res = results[0]
        r_string = res
        commodity_codes = commodities[res]
    else:
        for res in results:
            #r_string += res[0] + ";"
            r_string += res + ";"
            #commodity_codes += commodities[res[0]] + ";"
            commodity_codes += commodities[res] + ";"
    row.update({"Commodity": r_string, "Commodity Code": commodity_codes})
    print("Row " + row["id"] + ", commodities found.")
    return row

def get_brands():
    brands = []
    with open('brandlist.csv') as f:
        r = csv.DictReader(f)
        for row in r:
            if row["Brand"] != "":
                brands.append(row["Brand"].lower())
    return brands

def most_matching_words(description, commodities, limit, brands):
    jaccard_distance = {}
    for c in commodities:
        c_list = re.findall(r"[\w']+", c)
        c_list = [re.sub('\er$', '', re.sub('\ing$', '', w.lower().rstrip("s"))) for w in c_list]
        #Remove the brand names from the description
        c_list = list(set(c_list) - set(brands))
        d_list = re.findall(r"[\w']+", description)
        d_list = [re.sub('\er$', '', re.sub('\ing$', '', w.lower().rstrip("s"))) for w in d_list]
        intersection = len(set(c_list).intersection(set(d_list)))
        jaccard_distance[c] = intersection / (len(c_list) + len(d_list) - intersection)
    commodities_sorted = sorted(list(jaccard_distance.keys()), key = lambda commodity: -jaccard_distance[commodity])
    return commodities_sorted[:limit]

def generate_segment_files():
    if os.path.isdir("segment_files/"):
        return
    os.mkdir("segment_files")
    with open('unspsc_codes_3.csv') as f:
        r = csv.DictReader(f)
        prev_seg = ""
        rows = []
        for row in r:
            curr_seg = row['Segment Name']
            if curr_seg != prev_seg and prev_seg != "":
                print(curr_seg)
                file_util.save_csv("segment_files/" + prev_seg + ".csv", rows, mode="a")
                rows = []
            else:
                rows.append(row)
            prev_seg = curr_seg
        file_util.save_csv("segment_files/" + prev_seg + ".csv", rows, mode="a")


def segment_to_string(segment_name):
    family_names = []
    class_names = []
    commodity_names = []
    with open("segment_files/" + segment_name + ".csv") as f:
        r = csv.DictReader(f)
        for row in r:
            fam = row["Family Name"]
            cl = row["Class Name"]
            com = row["Commodity Name"]
            if not fam in family_names:
                family_names.append(fam)
            if not cl in class_names:
                class_names.append(cl)
            if not com in commodity_names:
                commodity_names.append(com)
    seg_str = segment_name + " " + str(family_names) + " " + str(class_names) + " " + str(commodity_names)
    seg_str = seg_str.replace("[", "").replace("]", "").replace("'", "").replace(",", "").lower()
    return seg_str

def segment_names():
    files = os.listdir("segment_files")
    segments = []
    for f in files:
        seg = f.replace(".csv", "")
        if "~lock" not in seg:
            segments.append(seg)
    return segments

def generate_segment_string_csv():
    if os.path.isfile("segment_strings.csv"):
        return
    segs = segment_names()
    for s in segs:
        print(s)
        row = {"Segment Name": s, "Segment String": segment_to_string(s)}
        file_util.save_csv("segment_strings.csv", [row])

def generate_preprocessed_stocks_csv(stock_master):
    descriptions = {}
    brands = {}
    forbidden_characters = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    for i, row in enumerate(stock_master):
        d_orig = row["text"]
        d_splits = re.findall(r"[\w']+", d_orig)
        d = ""
        for s in d_splits:
            if not any(c in s for c in forbidden_characters):
                d += s + " "
        if d == "":
            d = d_orig
        if not d in descriptions:
            descriptions[d] = [row["id"]]
            brands[d] = [row["Brand"]]
        else:
            descriptions[d] = descriptions[d] + [row["id"]]
            brands[d] = brands[d] + [row["Brand"]]
    rows = []
    for d in descriptions:
        row_numbers = ""
        bs = ""
        for rn in descriptions[d]:
            row_numbers += str(rn) + ";"
        for b in brands[d]:
            bs += str(b) + ";"
        row = {"Description": d, "id": row_numbers, "Brands": bs}
        rows.append(row)
    return rows

def count_field(stock_master, field):
    brands = {}
    for row in stock_master:
        b = row[field]
        if not b in brands:
            brands[b] = 1
        else:
            brands[b] += 1
    rows = []
    for b in brands:
        row = {"Brand": b, "Count": brands[b]}
        rows.append(row)
    return rows

def save_brands(rows, filename):
    file_util.save_csv(filename, rows, mode="w", fieldnames = ["Brand", "Count"])

def map_preprocessed_to_original(combined_stocks, stocks_with_commodities):
    stocks = {}
    r1 = csv.DictReader(f1)
    print("Generating dictionary from the original data..")
    for row in combined_stocks:
        print("Row id: " + row["id"])
        stocks[int(row["id"])] = row
    r2 = csv.DictReader(f2)
    for row in stocks_with_commodities:
        ids = filter(None, row["id"].split(";"))
        for i in ids:
            print("Updating row id: " + i)
            stocks[int(i)].update({"Commodity Code": row["Commodity Code"], "Commodity": row["Commodity"]})
    rows = []
    ids = list(stocks.keys())
    ids.sort()
    for i in ids:
        rows.append(stocks[i])
    fieldnames = ["", "id", "language", "text", "Brand", "Commodity", "Commodity Code"]
    return (rows, fieldnames)

def remove_temp_files():
    tmp_files = ["brand_counts.csv", "brands_to_segments.csv", "preprocessed_stocks_with_brands.csv", "segment_strings.csv", "stock_with_commodities.csv", "stock_with_segments.csv"]
    for f in tmp_files:
        os.remove(f)

def add_commodities_to_stocks_with_files():
    #generate_segment_files() # CONSTANT
    #generate_segment_string_csv() # CONSTANT

    if not os.path.isfile("preprocessed_stocks_with_brands.csv"):
        rows = generate_preprocessed_stocks_csv("combined_stock_master_withbrands.csv")
        file_util.save_csv("preprocessed_stocks_with_brands.csv", rows, mode="w", fieldnames = ["Description", "id", "Brands"])

    if not os.path.isfile("brand_counts.csv"):
        brand_counts = count_field("combined_stock_master_withbrands.csv", "Brand")
        save_brands(brand_counts, "brand_counts.csv")

    if not os.path.isfile("brands_to_segments.csv"):
        rows = brands_to_segments.brands_to_segments("brand_counts.csv", "preprocessed_stocks_with_brands.csv")
        brands_to_segments.save_segments(rows, "brands_to_segments.csv")
    if not os.path.isfile("stock_with_segments.csv"):
        rows = embedding_match.embedding_match('segment_strings.csv', "brands_to_segments.csv", 'preprocessed_stocks_with_brands.csv')
        embedding_match.csv_write('stock_with_segments.csv', rows)

    rows = match_commodities('stock_with_segments.csv')
    output_file = "stock_with_commodities.csv"
    print("Saving to " + output_file)
    file_util.save_csv(output_file, rows, mode="w")

    rows, fieldnames = map_preprocessed_to_original("combined_stock_master_withbrands.csv", "stock_with_commodities.csv")
    print("Saving to combined_stock_master_withbrands_and_commodities.csv..")
    file_util.save_csv("combined_stock_master_withbrands_and_commodities.csv", rows, fieldnames = fieldnames, mode = "w")
    print("Done.")

    remove_temp_files()

def add_commodities_to_stocks(stock_master):
    preprocessed = generate_preprocessed_stocks_csv(stock_master)
    brand_counts = count_field(stock_master, "Brand")
    segment_strings = file_util.read_csv("segment_strings.csv")
    brands_segs = brands_to_segments.brands_to_segments(segments_strings, brand_counts, preprocessed)
    stock_with_segments = embedding_match.embedding_match(segment_strings, brands_segs, preprocessed)
    stock_with_commodities = match_commodities(stock_with_segments)
    rows, fieldnames = map_preprocessed_to_original(stock_master, stock_with_commodities)
    return (rows, fieldnames)

if __name__=="__main__":
    stock_master = file_util.read_csv("combined_stock_master_withbrands.csv")
    add_commodities_to_stocks(stock_master)
    #description = "MOTOR WIPER"
    #commodities = ["motor oil", "wiper motor", "my foot"]
    #limit = 2
    #print(most_matching_words(description, commodities, limit))
    #map_preprocessed_to_original()
    #match_commodities()
    #generate_preprocessed_stocks_csv()
    #brands = count_brands()
    #save_brands(brands)
