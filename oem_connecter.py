import file_utils
import csv_scripts
from collections import defaultdict
import concurrent.futures
import sys
import time

def generate_dict(site_rows):
    oem_dict = {}
    for site, rows in site_rows.items():
        oem_dict = update_oem_dict(site, oem_dict, rows)
    return oem_dict

def update_oem_dict(site, oem_dict, rows):
    for row in rows:
        oem_code = row["OEM Field"]
        if oem_code in oem_dict:
            single_oem = oem_dict[oem_code]
        else:
            single_oem = {}
        single_oem[site] = {"Description": row["Stock Description"], "Code": row["Stock Code"], "Item #": row["Item #"]}
        oem_dict[oem_code] = single_oem
    return oem_dict

def match_by_oem_code(oem_dict, rows):
    for row in rows:
        oem_code = row["OEM Code"]
        if oem_code in oem_dict:
            oem_matches = oem_dict[oem_code]
            for site, match in oem_matches.items():
                row["{} OEM Code Match".format(site)] = match["Item #"]
    return rows

def base_rows_from(site_rows):
    base_rows = []
    for site, rows in site_rows.items():
        for row in rows:
            base_row = {}
            base_row["Site"] = site
            base_row["Item #"] = row["Item #"]
            base_row["OEM Code"] = row["OEM Field"]
            base_row["Stock Code"] = row["Stock Code"]
            base_row["Description"] = row["Stock Description"]
            base_rows.append(base_row)
    return base_rows


def preprocess_all(site_rows):
    site_to_descs = {}
    for site, rows in site_rows.items():
        desc_to_preprocessed = {}
        for row in rows:
            desc = row["Stock Description"]
            relevant_data = {"Preprocessed": preprocess(desc), "OEM Code": row["OEM Field"], "Stock Code": row["Stock Code"], "Item #": row["Item #"]}
            desc_to_preprocessed[desc] = relevant_data
        site_to_descs[site] = desc_to_preprocessed
    return site_to_descs

def preprocess(string):
    return set(string.replace(";", "").lower().split(" "))

def exclude_matches(site_rows, oem_dict):
    no_matches = {}
    for site in site_rows:
        rows = site_rows[site]
        site_no_matches = []
        for row in rows:
            for site2 in site_rows:
                oem_code = row["OEM Field"]
                if site2 not in oem_dict[oem_code] or oem_code == "ZZDELETED" or not oem_code:
                   site_no_matches.append(row)
                   break
        no_matches[site] = site_no_matches
    return no_matches

def match_by_description(oem_dict, site_rows):
    print("Match_by_description")
    site_rows = exclude_matches(site_rows, oem_dict)
    site_to_descs_preprocessed = preprocess_all(site_rows)
    jobs = {}
    count = 0
    desc_matches = {}
    a_set = set()
    for home, rows in site_rows.items():
        for row in rows:
            row_jobs = {}
            preprocessed = preprocess(row["Stock Description"])
            for site in site_rows:
                oem_code = row["OEM Field"]
                if site not in oem_dict[oem_code] or oem_code == "ZZDELETED" or not oem_code:
                    row_jobs[site] = csv_scripts.most_matching_words(preprocessed, site_to_descs_preprocessed[site], 10, a_set)
            jobs[row["Item #"]] = row_jobs
            #if count > 100:
            #    break
            #else:
            #    count += 1
    for item_no, item_jobs in jobs.items():
        for site, job in item_jobs.items():
            results, scores = job #job.result()
            if str(item_no) not in desc_matches:
                desc_matches[str(item_no)] = {}
            #site_to_descs_preprocessed[site][results[0]]["Item #"]
            desc_matches[str(item_no)][site] = {"Matches": [site_to_descs_preprocessed[site][result]["Item #"] for result in results], "Scores": [score for score in scores]}
    return desc_matches

def number(rows, start):
    num = start
    for row in rows:
        row["Item #"] = str(num)
        num += 1
    return rows, num

def match_oems(site_rows, matches_json=""):
    site_rows["FQMO"], num = number(site_rows["FQMO"], start = 0)
    site_rows["Kalumbila"], num = number(site_rows["Kalumbila"], start = num)
    oem_dict = generate_dict(site_rows)
    sites = site_rows.keys()
    rows = base_rows_from(site_rows)
    rows = match_by_oem_code(oem_dict, rows)
    if matches_json and file_utils.file_exists(matches_json):
        desc_matches = file_utils.read_json(matches_json)
    else:
        desc_matches = match_by_description(oem_dict, site_rows)
        if matches_json:
            file_utils.save_json(matches_json, desc_matches)
    for row in rows:
        for site in site_rows:
            if site in row:
                row[site + " Score"] = 1.0
        item_no = row["Item #"]
        if str(item_no) in desc_matches:
            for site, matches in desc_matches[item_no].items():
                for i, (match, score) in enumerate(zip(matches["Matches"], matches["Scores"])):
                    row["{} Description Match {}".format(site, str(i))] = match
                    row["{} Description Match {} Score".format(site, str(i))] = score
    fieldnames = ["Site", "Item #", "OEM Code", "Stock Code", "Description"]
    for site in sorted(list(site_rows.keys())):
        fieldnames.append("{} OEM Code Match".format(site))
        for i in range(10):
            fieldnames.append("{} Description Match {}".format(site, str(i)))
            fieldnames.append("{} Description Match {} Score".format(site, str(i)))
    print(fieldnames)

    return (rows, fieldnames)

if __name__=="__main__":
    if len(sys.argv) < 4:
        print("""
        Script to match similar rows in data from different sites.

        Use: $ python oem_connecter.py site1.csv site2.csv ouput.csv (optional)match_data.json

        Generating the description matches in match_data is by far the slowest part, so save it when expecting to re-use!
        """)
        sys.exit()
    sqmo_file = sys.argv[1] #"FQMO.csv"
    kalumbila_file = sys.argv[2] #"Kalumbila.csv"
    output_file = sys.argv[3] #"OEM_Match_Results.csv"
    matches_json = ""
    if len(sys.argv) == 5:
        matches_json = sys.argv[4]
    fqmo_rows = file_utils.read_csv(sqmo_file)
    kalumbila_rows = file_utils.read_csv(kalumbila_file)
    site_rows = {"FQMO": fqmo_rows, "Kalumbila": kalumbila_rows}
    result_rows, fieldnames = match_oems(site_rows, matches_json)
    file_utils.save_csv(output_file, result_rows, fieldnames=fieldnames)
