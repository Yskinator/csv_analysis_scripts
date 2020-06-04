import os
import sys
import csv
import copy
import concurrent.futures
import regex as re
# if "LOCAL" in os.environ:
import file_utils
import top_category_matcher
# else:
#     from . import file_utils
#     from . import top_category_matcher

csv.field_size_limit(int(sys.maxsize/100000000000))

#Requires csv:s generated by generate_top_category_files to be in top_category_files/
def match_commodities(stock_with_top_categories, jaccard_threshold):
    rows = []
    brands = get_brands()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for row in stock_with_top_categories:
            futures.append(executor.submit(match_commodities_for_row, row, jaccard_threshold, brands))
        for future in futures:
            updated_row = future.result()
            rows.append(updated_row)
    return rows

def get_commodities_for_top_categories(top_categories):
    """Given a list of top categories:
        (1) go through the matching files and
        (2) compose a list of all commodities contained in those files.

        Arguments:
        top_categories -- list of names of top categories to fetch

        Returns:
        List of commodities in the given top categories."""
    commodities = {}
    for top_cat in top_categories:
        with open("top_category_files/" + top_cat + ".csv") as f:
            r = csv.DictReader(f)
            for row in r:
                if row["Commodity Name"] in commodities:
                    print("Duplicate commodity: " + row["Commodity Name"])
                commodities[row["Commodity Name"]] = row["Commodity"]
    return commodities

def match_commodities_for_row(row, jaccard_threshold, brands=[]):
    desc = row["Description"]
    print("Row " + row["id"] + ", matching commodities.")
    tc_string = row["Top Categories"].replace('"', "")
    tcs = filter(None, tc_string.split(";"))
    commodities = get_commodities_for_top_categories(tcs)
    results, scores = most_matching_words(desc, list(commodities), limit=1, brands=brands)

    #RE-RUN MATCHING IF LOW JACCARD SCORES
    if scores[0] < jaccard_threshold:
        #Get ALL top_category files
        tcs = top_category_matcher.excluded_top_categories(return_excluded=False)
        commodities = get_commodities_for_top_categories(tcs)
        results, scores = most_matching_words(desc, list(commodities), limit=1, brands=brands)

    if len(results) == 1:
        res = results[0]
        sc = round(scores[0], 2)
        r_string = res
        commodity_codes = commodities[res]
    else:
        r_string = ""
        commodity_codes = ""
        commodities["NOT FOUND"] = ""
        for res in results:
            r_string += res + ";"
            commodity_codes += commodities[res] + ";"
            sc = scores

    row.update({"Commodity": r_string, "Commodity Code": commodity_codes, "Jaccard": sc})
    print("Row " + row["id"] + ", commodities found.")
    return row

def get_brands():
    brands = []
    with open('brand_counts.csv') as f:
        r = csv.DictReader(f)
        for row in r:
            if row["Brand"] != "":
                brands.append(row["Brand"].lower())
    return brands

def most_matching_words(description, commodities, limit, brands):
    '''
    Function to calculate Jaccard distance between individual words
    INPUTS:
     - description:
     - commodities
     - limit
     - brands
    OUTPUTS:
     - commodities_sorted[:limit]
     - scores_sorted[:limit]
    '''
    jaccard_distance = {}
    try:
        for c in commodities:
            c_list = re.findall(r"[\w]+", c)
            c_list = [re.sub('\er$', '', re.sub('\ing$', '', w.lower().rstrip("s"))) for w in c_list]
            #c_list = [re.sub('\er$', '', w.lower().rstrip("s")) for w in c_list]
            d_list = re.findall(r"[\w]+", description)
            d_list = [re.sub('\er$', '', re.sub('\ing$', '', w.lower().rstrip("s"))) for w in d_list]
            #d_list = [re.sub('\er$', '', w.lower().rstrip("s")) for w in d_list]
            #Remove the brand names from the description
            d_list = list(set(d_list) - set(brands))
            intersection = len(set(c_list).intersection(set(d_list)))
            jaccard_distance[c] = intersection / (len(c_list) + len(d_list) - intersection)
        commodities_sorted = sorted(list(jaccard_distance.keys()), key=lambda commodity: -jaccard_distance[commodity])
        scores_sorted = sorted(list(jaccard_distance.values()), reverse=True)
    except:
        commodities_sorted = ["NOT FOUND" for i in range(limit)]
    return commodities_sorted[:limit], scores_sorted[:limit]

def generate_top_category_files(column_name):
    if os.path.isdir("top_category_files/"):
        print("top_category_files/ directory already exists")
        return
    os.mkdir("top_category_files")
    with open('unspsc_codes_v3.csv') as f:
        r = csv.DictReader(f)
        tcs = {}
        for row in r:
            if row[column_name] not in tcs:
                tcs[row[column_name]] = []
            tcs[row[column_name]].append(row)
        for tc in tcs:
            filename = "top_category_files/" + tc + ".csv"
            print("Saving " + filename)
            file_utils.save_csv(filename, tcs[tc])

def top_category_to_string(top_category_name):
    segment_names = []
    family_names = []
    class_names = []
    commodity_names = []
    with open("top_category_files/" + top_category_name + ".csv") as f:
        r = csv.DictReader(f)
        for row in r:
            seg = row["Segment Name"]
            fam = row["Family Name"]
            cl = row["Class Name"]
            com = row["Commodity Name"]
            if not seg in segment_names:
                segment_names.append(seg)
            if not fam in family_names:
                family_names.append(fam)
            if not cl in class_names:
                class_names.append(cl)
            if not com in commodity_names:
                commodity_names.append(com)
    tc_str = str(segment_names) + " " + str(family_names) + " " + str(class_names) + " " + str(commodity_names)
    tc_str = tc_str.replace("[", "").replace("]", "").replace("'", "").replace(",", "").lower()
    return tc_str

def generate_top_category_string_csv():
    if os.path.isfile("top_category_strings.csv"):
        print("top_category_strings.csv file already exists")
        return
    tcs = file_utils.top_category_names()
    rows = []
    for s in tcs:
        print(s)
        row = {"Top Category Name": s, "Top Category String": top_category_to_string(s)}
        rows.append(row)
    file_utils.save_csv("top_category_strings.csv", rows)

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

def map_preprocessed_to_original(combined_stocks, stocks_with_commodities):
    stocks = {}
    print("Generating dictionary from the original data..")
    for row in combined_stocks:
        print("Row id: " + row["id"])
        stocks[int(row["id"])] = row
    for row in stocks_with_commodities:
        ids = filter(None, row["id"].split(";"))
        for i in ids:
            print("Updating row id: " + i)
            stocks[int(i)].update({"Commodity Code": row["Commodity Code"], "Commodity": row["Commodity"], "Jaccard": row["Jaccard"]})
    rows = []
    ids = list(stocks.keys())
    ids.sort()
    for i in ids:
        rows.append(stocks[i])
    fieldnames = ["", "id", "language", "text", "Brand", "Commodity", "Commodity Code", "Jaccard"]
    return (rows, fieldnames)

def remove_temp_files():
    tmp_files = ["brand_counts.csv", "brands_to_top_categories.csv", "preprocessed_stocks_with_brands.csv", "top_category_strings.csv", "stock_with_commodities.csv", "stock_with_top_categories.csv"]
    for f in tmp_files:
        os.remove(f)

def add_commodities_to_stocks(stock_master, level="Family Name", tc_to_check_count=25, jaccard_threshold = 0.3):
    """stock_master is a list of dicts that must contain keys id, text and Brand. Brand may be an empty string."""
    stock_master = copy.deepcopy(stock_master) # Protect input from side effects, parallelization makes changes in-place
    generate_constant_csvs(level)
    preprocessed = generate_preprocessed_stocks_csv(stock_master)
    brand_counts = count_field(stock_master, "Brand")
    top_category_strings = file_utils.read_csv("top_category_strings.csv")
    stock_with_top_categories = top_category_matcher.match_preprocessed_to_top_categories(preprocessed, top_category_strings, brand_counts, tc_to_check_count = tc_to_check_count)
    print("Matching commodities")
    stock_with_commodities = match_commodities(stock_with_top_categories, jaccard_threshold)
    rows, fieldnames = map_preprocessed_to_original(stock_master, stock_with_commodities)
    return (rows, fieldnames)

def generate_brand_counts_csv():
    if not os.path.isfile("brand_counts.csv"):
        stock_master = file_utils.read_csv("combined_stock_master_withbrands.csv")
        brands = count_field(stock_master, "Brand")
        file_utils.save_csv("brand_counts.csv", brands, fieldnames=["Brand", "Count"])

def generate_constant_csvs(level="Family Name"):
    generate_top_category_files(level)
    generate_top_category_string_csv()
    generate_brand_counts_csv()

if __name__ == "__main__":
    import sys
    import time
    if len(sys.argv) != 4:
        print("""
        Script to allocate items to a UNSPSC product

        Use: $ python csv_scripts.py filename.csv level[Segment, Family, Class] num_to_check[int]

        """)
        sys.exit()

    stime = time.time()
    stock_master = file_utils.read_csv(sys.argv[1])
    level = sys.argv[2]

    if len(sys.argv) > 3:
        top_categories_to_check_count = int(sys.argv[3])
    else:
        top_categories_to_check_count = 100

    rows, fieldnames = add_commodities_to_stocks(stock_master, level+" Name", top_categories_to_check_count)
    file_utils.save_csv(sys.argv[1].split(".csv")[0]+"_and_commodities.csv", rows, fieldnames=fieldnames)

    etime = time.time()
    ttime = etime-stime
    print('Time = ', ttime, 's')
