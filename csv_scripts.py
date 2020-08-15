import os
import sys
import csv
import concurrent.futures
import regex as re
# if "LOCAL" in os.environ:
import file_utils
import top_category_matcher
# else:
#     from . import file_utils
#     from . import top_category_matcher

csv.field_size_limit(int(sys.maxsize/100000000000))

def match_commodities(stock_with_top_categories, jaccard_threshold, parallel=True):
    """Match commodities to stocks.
    Requires csv:s generated by generate_top_category_files to be in top_category_files/.

    Arguments:
    stock_with_top_categories -- A list of dictionaries, each with keys "Description", "id", "Top Categories", and "Brands".
    jaccard_threshold (float) -- if jaccard_index is lower than threshold, re-run with all top categories.
    parallel (boolean) -- Whether to use concurrency or not. Defaults to True.

    Returns:
    List of dictionaries with the same keys as stock_with_top_categories, and the keys "Commodity", "Commodity Code", and "Jaccard".
    """
    brands = get_brands()
    #Fetches all the allowed top categories.
    tcs = top_category_matcher.excluded_top_categories(return_excluded=False)
    commodities = {tc: get_commodities_for_top_category(tc) for tc in tcs}
    if parallel:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = []
            for row in stock_with_top_categories:
                futures.append(executor.submit(match_commodities_for_row, row, jaccard_threshold, commodities, brands))
            updated_rows = [future.result() for future in futures]
    else:
        updated_rows = [match_commodities_for_row(row, jaccard_threshold, commodities, brands) for row in stock_with_top_categories]
    return updated_rows

def get_commodities_for_top_category(top_category):
    return get_commodities_for_top_categories([top_category])

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
                commodities[row["Commodity Name"]] = {"Commodity Code": row["Commodity"], "Preprocessed": to_base_word_set(row["Commodity Name"])}
    return commodities

def match_commodities_for_row(row, jaccard_threshold, commodities_by_tc, brands=[]):
    desc = to_base_word_set(row["Description"])
    brands = set(brands)
    print("Row " + row["id"] + ", matching commodities.")
    tc_string = row["Top Categories"].replace('"', "")
    tcs = filter(None, tc_string.split(";"))
    commodities = {}
    for tc in tcs:
        commodities.update(commodities_by_tc[tc])
    results, scores = most_matching_words(desc, sentences_preprocessed=commodities, number_of_results=1, words_to_exclude=brands)

    #RE-RUN MATCHING IF LOW JACCARD SCORES
    if scores[0] < jaccard_threshold:
        #Get ALL top_category files minus the ones we checked before
        print("Low Jaccard score, checking other categories.")
        tcs = set(commodities_by_tc.keys()) - set(tcs)
        commodities = {}
        for tc in tcs:
            commodities.update(commodities_by_tc[tc])
        more_results, more_scores = most_matching_words(desc, sentences_preprocessed=commodities, number_of_results=1, words_to_exclude=brands)
        #{**x, **y} merges two dictionaries
        jaccard_scores_dict_all_results = {**dict(zip(results, scores)), **dict(zip(more_results, more_scores))}
        results, scores = best_n_results(jaccard_scores_dict_all_results, n=1)

    if len(results) == 1:
        res = results[0]
        sc = round(scores[0], 2)
        r_string = res
        commodity_codes = commodities[res]["Commodity Code"]
    else:
        r_string = ""
        commodity_codes = ""
        commodities["NOT FOUND"] = ""
        for res in results:
            r_string += res + ";"
            commodity_codes += commodities[res]["Commodity Code"] + ";"
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

def to_base_word_set(string):
    words = re.findall(r"[\w]+", string)
    base_words = [re.sub('\er$', '', re.sub('\ing$', '', w.lower().rstrip("s"))) for w in words]
    return set(base_words)

def most_matching_words(words_to_match, sentences_preprocessed, number_of_results, words_to_exclude):
    '''
    Function to calculate Jaccard distance between individual words.
    Preprocess words_to_match and sentences_preprocessed with to_base_word_set().
    sentences_preprocessed should be a {string: {"Preprocessed": to_base_word_set(string)}} dictionary.
    INPUTS:
     - words_to_match
     - sentences_preprocessed
     - number_of_results
     - words_to_exclude
    OUTPUTS:
     - matches_sorted[:limit]
     - scores_sorted[:limit]
    '''
    print("Matching " + str(words_to_match))
    jaccard_index = {}
    try:
        for match_candidate in sentences_preprocessed:
            preprocessed_candidate = sentences_preprocessed[match_candidate]["Preprocessed"]
            words_to_match -= words_to_exclude
            intersection = len(preprocessed_candidate.intersection(words_to_match))
            jaccard_index[match_candidate] = intersection / (len(preprocessed_candidate) + len(words_to_match) - intersection)
        matches_sorted, scores_sorted = best_n_results(jaccard_index, number_of_results)
    except:
        matches_sorted = ["NOT FOUND" for i in range(number_of_results)]
        scores_sorted = [0 for i in range(number_of_results)]
    print("Finished " + str(words_to_match))
    return matches_sorted[:number_of_results], scores_sorted[:number_of_results]

def best_n_results(jaccard_index, n):
    commodities_sorted = sorted(list(jaccard_index.keys()), key=lambda commodity: -jaccard_index[commodity])
    scores_sorted = sorted(list(jaccard_index.values()), reverse=True)
    return commodities_sorted[:n], scores_sorted[:n]


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
    """Preprocess stocks from stock_master, combining rows with identical descriptions reversibly.
    If rows with ids 1 and 2 have the same description, combines them into one row with id "1;2".

    Arguments:
    stock_master -- A list of dictionaries, each with keys "text", "id", "Brand".

    Returns:
    A list of dictionaries, each with keys "Description", "id", and "Brands".
    """
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
        # Use copy here to avoid modifying the input
        stocks[int(row["id"])] = row.copy()
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

def add_commodities_to_stocks(stock_master, level="Family Name", tc_to_check_count=25, jaccard_threshold = 0.3, parallel=True):
    """stock_master is a list of dicts that must contain keys id, text and Brand. Brand may be an empty string."""
    generate_constant_csvs(level)
    preprocessed = generate_preprocessed_stocks_csv(stock_master)
    brand_counts = count_field(stock_master, "Brand")
    top_category_strings = file_utils.read_csv("top_category_strings.csv")
    stock_with_top_categories = top_category_matcher.match_preprocessed_to_top_categories(preprocessed, top_category_strings, brand_counts, tc_to_check_count = tc_to_check_count)
    print("Matching commodities")
    stock_with_commodities = match_commodities(stock_with_top_categories, jaccard_threshold, parallel)
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
