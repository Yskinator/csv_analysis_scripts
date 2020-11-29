import argparse
import concurrent.futures
import pandas
import sys
import time
import copy

from collections import defaultdict, OrderedDict

import file_utils
from matcher import preprocess, most_matching_words

OUTPUT_FIELDNAMES = ["Site", "Match Site", "Stock & Site", "Description", "Old Row", "Match Description", "Match Stock & Site", "Match Score", "Match Number", "Matching Row Count"]

INPUT_FIELDNAMES = ["Site", "Stock Code", "Stock & Site", "Stock Description"]

ALL_FIELDNAMES = list(set(INPUT_FIELDNAMES) | set(OUTPUT_FIELDNAMES))

def base_rows_from(site_rows):
    base_rows = []
    for site, rows in site_rows.items():
        for row in rows:
            base_row = {}
            base_row["Site"] = site
            base_row["Stock & Site"] = row["Stock & Site"]
            base_row["Stock Code"] = row["Stock Code"]
            base_row["Description"] = row["Stock Description"]
            base_rows.append(base_row)
    return base_rows

def generate_item_ids_to_rows(rows):
    item_ids_to_rows = {}
    for row in rows:
        item_id = row["Stock & Site"]
        if item_id not in item_ids_to_rows:
            item_ids_to_rows[item_id] = []
        item_ids_to_rows[item_id].append(row)
    return item_ids_to_rows

def preprocess_all(site_rows):
    site_to_descs = {}
    abbrevs = get_abbrevs()
    for site, rows in site_rows.items():
        desc_to_preprocessed = {}
        for row in rows:
            desc = row["Stock Description"].strip()
            if desc not in desc_to_preprocessed:
                relevant_data = {"Preprocessed": preprocess(desc, abbrevs), "Stock Code": row["Stock Code"], "Stock & Site": {row["Stock & Site"]}}
                desc_to_preprocessed[desc] = relevant_data
            else:
                desc_to_preprocessed[desc]["Stock & Site"].add(row["Stock & Site"])
        site_to_descs[site] = desc_to_preprocessed
    return site_to_descs

def get_abbrevs():
    abbrevs = file_utils.read_csv("desc_abbrevs.csv")
    for abbrev in abbrevs:
        abbrev["Abbreviation"] = abbrev["Abbreviation"].lower()
        abbrev["Expanded"] = abbrev["Expanded"].lower()
    return abbrevs

def generate_jobs(site_rows, site_to_descs_preprocessed):
    jobs = {}
    abbrevs = get_abbrevs()
    for home, rows in site_rows.items():
        for row in rows:
            row_jobs = {}
            desc = row["Stock Description"]
            desc = desc.strip()
            preprocessed = preprocess(desc, abbrevs)
            for site in site_to_descs_preprocessed:
                row_jobs[site] = most_matching_words(preprocessed, site_to_descs_preprocessed[site], 10, words_to_exclude=set())
            jobs[row["Stock & Site"]] = row_jobs
    return jobs

def match_by_description(site_rows, old_site_rows):
    site_to_descs_preprocessed = preprocess_all(site_rows)
    old_site_to_descs_preprocessed = preprocess_all(old_site_rows)
    all_site_to_descs_preprocessed = {}
    for site in (set(site_to_descs_preprocessed.keys()) | set(old_site_to_descs_preprocessed.keys())):
        all_site_to_descs_preprocessed[site] = {}
        if site in site_to_descs_preprocessed:
            all_site_to_descs_preprocessed[site].update(site_to_descs_preprocessed[site])
        if site in old_site_to_descs_preprocessed:
            all_site_to_descs_preprocessed[site].update(old_site_to_descs_preprocessed[site])
    desc_matches = {}
    jobs_new_to_new = generate_jobs(site_rows, site_to_descs_preprocessed)
    jobs_new_to_old = generate_jobs(site_rows, old_site_to_descs_preprocessed)
    jobs_old_to_new = generate_jobs(old_site_rows, site_to_descs_preprocessed)
    nn_desc_matches = jobs_to_desc_matches(jobs_new_to_new, all_site_to_descs_preprocessed)
    no_desc_matches = jobs_to_desc_matches(jobs_new_to_old, all_site_to_descs_preprocessed)
    on_desc_matches = jobs_to_desc_matches(jobs_old_to_new, all_site_to_descs_preprocessed)
    desc_matches = combine_desc_matches(nn_desc_matches, no_desc_matches, 10)
    desc_matches = combine_desc_matches(desc_matches, on_desc_matches, 10)
    return desc_matches

def jobs_to_desc_matches(jobs, all_site_to_descs_preprocessed):
    desc_matches = {}
    for item_id, item_jobs in jobs.items():
        for site, job in item_jobs.items():
            results, scores = job
            #results, scores = job.result()
            if str(item_id) not in desc_matches:
                desc_matches[str(item_id)] = {}
            #site_to_descs_preprocessed[site][results[0]]["Stock & Site"]
            #desc_matches[str(item_id)][site] = {"Matches": [site_to_descs_preprocessed[site][result]["Stock & Site"] for result in results], "Scores": [score for score in scores]}
            desc_matches[str(item_id)][site] = {"Matches": results, "Scores": scores, "Stock & Site": []}
            for result in results:
                stock_and_site = all_site_to_descs_preprocessed[site][result]["Stock & Site"]
                desc_matches[str(item_id)][site]["Stock & Site"].append(stock_and_site)
    return desc_matches

def combine_desc_matches(matches1, matches2, n):
    """Combine description matches. Input and output is like {"item_id1": {"site1": {"Matches": [...], "Scores": [...], "Stock & Site": [...]}, ...}, ...}

    Arguments:
    matches1, matches2 -- Lists of dictionaries mapping item_ids ("Stock & Site" fields) to sites to matches.
    n -- The amount of matches to return for each item_id and site

    Returns:
    A dict of dicts of dicts mapping item_ids to sites to matches.
    """
    results = {}
    if not matches1:
        return matches2
    if not matches2:
        return matches1
    item_ids = set(matches1.keys()) | set(matches2.keys())
    for item_id in item_ids:
        if item_id not in matches1:
            results[item_id] = matches2[item_id]
            continue
        if item_id not in matches2:
            results[item_id] = matches1[item_id]
            continue
        sites = set(matches1[item_id].keys()) | set(matches2[item_id].keys())
        results[item_id] = {}
        for site in sites:
            if site not in matches1[item_id]:
                results[item_id][site] = matches2[item_id][site]
                continue
            if site not in matches2[item_id]:
                results[item_id][site] = matches1[item_id][site]
                continue
            m1 = matches1[item_id][site]
            m2 = matches2[item_id][site]
            results[item_id][site] = top_n_matches(m1, m2, n)
    return results

def top_n_matches(m1, m2, n):
    """Return the best n matches in m1 and m2.

    Arguments:
    m1, m2 -- Dictionaries with keys "Matches", "Scores" and "Stock & Site" mapped to lists of equal length
    n (integer) -- The amount of matches to return

    Returns:
    A dictionary with keys "Matches", "Scores" and "Stock & Site" mapped to lists, combining m1 and m2 while removing duplicates. The lists are sorted and of length n.
    """
    all_matches = list(zip(m1["Matches"], m1["Scores"], m1["Stock & Site"])) + list(zip(m2["Matches"], m2["Scores"], m2["Stock & Site"]))
    all_matches = sorted(all_matches, key = lambda match: float(match[1]), reverse = True)
    #all_matches = list(OrderedDict.fromkeys(all_matches)) #Remove duplicates
    descs = []
    no_duplicate_matches = []
    for match in all_matches:
        if not match[0] in descs:
            descs.append(match[0])
            no_duplicate_matches.append(match)
        else:
            #Update our list of rows this description matches to
            match_index = descs.index(match[0])
            rows = no_duplicate_matches[match_index][2]
            prev_match = no_duplicate_matches[match_index]
            rows = rows.union(match[2])
            new_match = (prev_match[0], prev_match[1], rows)
            no_duplicate_matches[match_index] = new_match
    result_matches = {"Matches": [], "Scores": [], "Stock & Site": []}
    for match in no_duplicate_matches[:n]:
        result_matches["Matches"].append(match[0])
        result_matches["Scores"].append(match[1])
        result_matches["Stock & Site"].append(match[2])
    return result_matches


def number(rows, start):
    num = start
    for row in rows:
        row["Item #"] = str(num)
        num += 1
    return rows, num

def find_rows_with_id_and_match_site(old_item_ids_to_rows, item_id, match_site):
    results = []
    if item_id in old_item_ids_to_rows:
        for row in old_item_ids_to_rows[item_id]:
            if row["Match Site"] == match_site:
                results.append(row)
    return results

def match_sites2(site_rows, old_site_rows = {}, old_item_ids_to_rows = {}, matches_json="", exclude_unchanged = True):
    """A reimplementation of match_sites."""
    return []

def match_sites(site_rows, old_site_rows = {}, old_item_ids_to_rows = {}, matches_json="", exclude_unchanged = True):
    """Match rows to rows.

    Arguments:
    site_rows -- A dictionary mapping sites to lists of rows represented by dictionaries
    old_site_rows -- A dictionary mapping sites to lists of rows represented by dictionaries
    old_item_ids_to_rows -- A dictionary mapping item ids ("Stock & Site") to rows
    matches_json (string) -- A string representing the filename of a json file containing old matches to speed up processing
    exclude_unchanged (bool) -- If true, do not return rows which have not changed relative to old_site_rows

    Returns:
    A list of dictionaries representing rows with matches.
    """
    #num = 0
    #for site in site_rows:
    #    site_rows[site], num = number(site_rows[site], num)
    sites = set(site_rows.keys()) | set(old_site_rows.keys())
    rows = base_rows_from(site_rows)
    old_rows = base_rows_from(old_site_rows)
    rows = rows + old_rows
    if matches_json and file_utils.file_exists(matches_json):
        desc_matches = file_utils.read_json(matches_json)
    else:
        desc_matches = match_by_description(site_rows, old_site_rows)
        if matches_json:
            file_utils.save_json(matches_json, desc_matches)
    final_rows = []
    for row in rows:
        row = copy.deepcopy(row)
        item_id = str(row["Stock & Site"])
        all_sites = set()
        if item_id in desc_matches:
            all_sites = set(desc_matches[item_id])
        for site in all_sites:
            if site == row["Site"]:
                continue
            old_rows = find_rows_with_id_and_match_site(old_item_ids_to_rows, item_id, site)
            old_matches = {"Matches": [], "Scores": [], "Stock & Site": []}
            old_rows = sorted(old_rows, key = lambda r: r["Match Number"])
            for r in old_rows:
                if not r["Match Description"] in old_matches["Matches"]:
                    old_matches["Scores"].append(float(r["Match Score"]))
                    old_matches["Matches"].append(r["Match Description"])
                    old_matches["Stock & Site"].append(set())
                old_matches["Stock & Site"][-1].add(r["Match Stock & Site"])

            row_base = {"Stock & Site": item_id, "Site": row["Site"], "Description": row["Description"], "Match Site": site}

            matches = desc_matches[item_id][site]
            if matches == old_matches:
                if exclude_unchanged:
                    # Results unchanged for this site, skip to next one
                    continue
                row_base["Old Row"] = "Unchanged"
            else:
                matches = top_n_matches(matches, old_matches, 10)
                for old_row in old_rows:
                    old_row["Old Row"] = "Yes"
                    final_rows.append(old_row)
                row_base["Old Row"] = "No"
            for i, (match, score, desc_match_rows) in enumerate(zip(matches["Matches"], matches["Scores"], matches["Stock & Site"])):
                for match_row in desc_match_rows:
                    new_row = {**row_base, "Match Description": match, "Match Stock & Site": match_row, "Match Score": str(score), "Match Number": str(i), "Matching Row Count": str(len(desc_match_rows))}
                    #Prevent duplicate rows. TODO: Figure out how this happens.
                    #if not new_row in final_rows:
                    final_rows.append(new_row)

    return final_rows

def match_sites_dataframe(dataframe, matches_json=""):
    '''
    Generates a dataframe of matched sites.
    matches_json is an optional parameter for saving and loading slow to generate
    description based matches.
    INPUTS:
     - dataframe
     - matches_json
    OUTPUTS:
     - matches_df
    '''

    #Missing values should be represented by empty strings
    dataframe = dataframe.fillna(value="")

    #Ensure we have the correct columns
    dataframe = pandas.DataFrame(dataframe.to_dict("records"), columns=ALL_FIELDNAMES)

    #Fill any columns we just added with "-1" to mark it wasn't originally there
    dataframe = dataframe.fillna(value="-1")

    #Make sure everything in that dataframe is a string
    dataframe = dataframe.applymap(lambda x: str(x))

    #Remove extra whitespace
    dataframe = dataframe.applymap(lambda x: x.strip() if type(x)==str else x)

    if "Match Site" in dataframe.columns:
        ndf = dataframe[dataframe["Match Site"] == "-1"]
        if ndf.empty:
            #No new rows.
            return pandas.DataFrame()
        odf = dataframe[dataframe["Match Site"] != "-1"]
        # n = ndf.iloc[0]
        # ni = n.index[str(n).strip().replace(".0","") != "-1"]
        # ndf = ndf.loc[:, ni]
        if odf.empty:
            old_rows = []
        else:
            # o = odf.iloc[0]
            # oi = o.index[str(o).strip().replace(".0","") != "-1"]
            # odf = odf.loc[:, oi]
            old_rows = odf.to_dict("records")
        new_rows = ndf.to_dict("records")
    else:
        new_rows = dataframe.to_dict("records")
        old_rows = []
    #print(ndf.head(n=10))
    #print(odf.head(n=10))
    site_rows = generate_site_to_rows_dict(new_rows)
    old_site_rows = generate_site_to_rows_dict(old_rows, old=True)
    old_item_ids_to_rows = generate_item_ids_to_rows(old_rows)
    #print('from match_sites_dataframe')
    matches_rows = match_sites(site_rows, old_site_rows, old_item_ids_to_rows, matches_json)
    matches_df = pandas.DataFrame(matches_rows, columns=OUTPUT_FIELDNAMES)
    #matches_df['OEM Code Match'] = matches_df['OEM Code Match'].fillna(value="")
    matches_df = matches_df.fillna(value="")
    matches_df = matches_df[OUTPUT_FIELDNAMES]
    return matches_df

def generate_site_to_rows_dict(rows, old=False):
    """Generates site to rows dictionary.

    Arguments:
    rows -- A list of dictionaries representing rows
    old (bool) -- If True, change key "Description" to "Stock Description" and remove rows with duplicate "Stock & Site"

    Returns:
    A dictionary mapping each site to a list of rows related to that site
    """
    if old:
        item_ids = []
        new_rows = []
        for row in rows:
            row = copy.deepcopy(row)
            row["Stock Description"] = row["Description"]
            item_id = row["Stock & Site"]
            if item_id not in item_ids:
                item_ids.append(item_id)
                new_rows.append(row)
        rows = new_rows

    site_to_rows = {}
    sites = []
    for row in rows:
        row = copy.deepcopy(row)
        if row["Site"] not in site_to_rows:
            site_to_rows[row["Site"]] = []
        site_to_rows[row["Site"]].append(row)
    return site_to_rows

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Script to match similar rows in data from different sites.")
    parser.add_argument("filename", help="Filename of the csv file to process.")
    parser.add_argument("-o", "--output", help="Save output to file with the given filename. If argument is not present, the output is instead printed to console in an abbreviated form. If output file already exists, the new results are combined to the already existing ones.")
    parser.add_argument("-d", "--match_data", help="Filename of json with old matches. If file already exists, read it. If file does not exist, create one based on the results of this run. Generating the description matches in match_data is by far the slowest part, so it is recommended to save it when expecting re-use.")

    args = parser.parse_args()

    sites_rows = file_utils.read_csv(args.filename)
    output_file = args.output
    matches_json = args.match_data
    if not matches_json:
        matches_json = ""

    stime = time.time()

    if file_utils.file_exists(output_file):
        old_rows = file_utils.read_csv(output_file)
    else:
        old_rows = []
    site_rows = generate_site_to_rows_dict(sites_rows)
    old_site_rows = generate_site_to_rows_dict(old_rows, old=True)
    old_item_ids_to_rows = generate_item_ids_to_rows(old_rows)
    #site_rows = {"FQMO": fqmo_rows, "Kalumbila": kalumbila_rows}
    #site_to_dataframe_dict = {"FQMO": pandas.DataFrame(fqmo_rows), "Kalumbila": pandas.DataFrame(kalumbila_rows)}
    ndf = pandas.DataFrame(sites_rows)
    odf = pandas.DataFrame(old_rows)
    all_columns = ndf.columns.union(odf.columns)
    ndf = ndf.reindex(columns = all_columns, fill_value="-1")
    odf = odf.reindex(columns = all_columns, fill_value="-1")
    df = pandas.concat([ndf, odf]).reset_index(drop=True)
    #with pandas.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #    print(df)

    if output_file:
        matches_df = match_sites_dataframe(df, matches_json=matches_json)
        matches_df = matches_df.sort_values(by=["Stock & Site", "Match Stock & Site"])
        result_rows = matches_df.to_dict("records")
        file_utils.save_csv(output_file, result_rows, fieldnames=OUTPUT_FIELDNAMES)
    else:
        matches_df = match_sites_dataframe(df)
    with pandas.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(matches_df.head(n=10))
    #print(result_rows[:10])
    #exclude_unchanged = False
    #result_rows, fieldnames = match_sites(site_rows, old_site_rows, old_item_ids_to_rows, matches_json, exclude_unchanged)
    etime = time.time()
    ttime = etime-stime
    print('Time = ', ttime, 's')
