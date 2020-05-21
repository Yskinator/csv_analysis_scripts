import os
import csv
import re

def split_file():
    with open('unspsc_codes_3.csv') as f:
        r = csv.DictReader(f)
        prev_seg = ""
        rows = []
        for row in r:
            curr_seg = row['Segment Name']
            if curr_seg != prev_seg and prev_seg != "":
                print(curr_seg)
                save_file("csvs/" + prev_seg + ".csv", rows)
                rows = []
            else:
                rows.append(row)
            prev_seg = curr_seg
        save_file("csvs/" + prev_seg + ".csv", rows)

def save_file(filename, rows, mode = "a", fieldnames = ""):
    exists = False
    if os.path.isfile(filename) and mode == "a":
       exists = True
    with open(filename, mode) as  fo:
        if fieldnames == "":
            w = csv.DictWriter(fo, fieldnames = list(rows[0].keys()))
        else:
            w = csv.DictWriter(fo, fieldnames = fieldnames)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def segment_to_string(segment_name):
    family_names = []
    class_names = []
    commodity_names = []
    with open("csvs/" + segment_name + ".csv") as f:
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
    files = os.listdir("csvs")
    segments = []
    for f in files:
        seg = f.replace(".csv", "")
        if "~lock" not in seg:
            segments.append(seg)
    return segments

def generate_segment_string_csv():
    segs = segment_names()
    for s in segs:
        print(s)
        row = {"Segment Name": s, "Segment String": segment_to_string(s)}
        save_file("segment_strings.csv", [row])

def generate_preprocessed_stocks_csv():
    descriptions = {}
    brands = {}
    forbidden_characters = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    with open("combined_stock_master_withbrands.csv", "r") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
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
    save_file("preprocessed_stocks_with_brands.csv", rows, mode="w", fieldnames = ["Description", "id", "Brands"])

def count_brands():
    brands = {}
    with open("combined_stock_master_withbrands.csv", "r") as f:
        r = csv.DictReader(f)
        for row in r:
            b = row["Brand"]
            if not b in brands:
                brands[b] = 1
            else:
                brands[b] += 1
    return brands

def save_brands(brands):
    rows = []
    for b in brands:
        row = {"Brand": b, "Count": brands[b]}
        rows.append(row)
    save_file("brand_counts.csv", rows, mode="w", fieldnames = ["Brand", "Count"])





if __name__=="__main__":
    generate_preprocessed_stocks_csv()
    #brands = count_brands()
    #save_brands(brands)
