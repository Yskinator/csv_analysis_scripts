import file_utils
import csv_scripts
from collections import defaultdict, OrderedDict
import concurrent.futures
import pandas
import sys
import time
import copy

def generate_oem_dict(site_rows, old_site_rows):
    oem_dict = {}
    for site, rows in site_rows.items():
        oem_dict = update_oem_dict(site, oem_dict, rows)
    for site, rows in old_site_rows.items():
        oem_dict = update_oem_dict(site, oem_dict, rows)
    return oem_dict

def update_oem_dict(site, oem_dict, rows):
    for row in rows:
        oem_code = row["OEM Field"]
        if oem_code in oem_dict:
            single_oem = oem_dict[oem_code]
        else:
            single_oem = {}
        single_oem[site] = {"Description": row["Stock Description"], "Code": row["Stock Code"], "Stock & Site": row["Stock & Site"]}
        oem_dict[oem_code] = single_oem
    return oem_dict

def match_by_oem_code(oem_dict, rows):
    for row in rows:
        oem_code = row["OEM Code"]
        if oem_code in oem_dict:
            oem_matches = oem_dict[oem_code]
            for site, match in oem_matches.items():
                row["{} OEM Code Match".format(site)] = match["Stock & Site"]
    return rows

def base_rows_from(site_rows):
    base_rows = []
    for site, rows in site_rows.items():
        for row in rows:
            base_row = {}
            base_row["Site"] = site
            base_row["Stock & Site"] = row["Stock & Site"]
            base_row["OEM Code"] = row["OEM Field"]
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
    for site, rows in site_rows.items():
        desc_to_preprocessed = {}
        for row in rows:
            desc = row["Stock Description"]
            relevant_data = {"Preprocessed": preprocess(desc), "OEM Code": row["OEM Field"], "Stock Code": row["Stock Code"], "Stock & Site": row["Stock & Site"]}
            desc_to_preprocessed[desc] = relevant_data
        site_to_descs[site] = desc_to_preprocessed
    return site_to_descs

def preprocess(string):
    return set(string.replace(";", "").lower().split(" "))

def exclude_oem_matches(site_rows, oem_dict):
    #TODO: This looks broken. Investigate.
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

def generate_jobs(site_rows, site_to_descs_preprocessed, oem_dict):
    jobs = {}
    a_set = set()
    for home, rows in site_rows.items():
        for row in rows:
            row_jobs = {}
            preprocessed = preprocess(row["Stock Description"])
            oem_code = row["OEM Field"]
            descs_preprocessed = {}
            for site in site_to_descs_preprocessed:
                if site not in oem_dict[oem_code] or oem_code == "ZZDELETED" or not oem_code:
                    row_jobs[site] = csv_scripts.most_matching_words(preprocessed, site_to_descs_preprocessed[site], 10, a_set)
            jobs[row["Stock & Site"]] = row_jobs
    return jobs

def match_by_description(oem_dict, site_rows, old_site_rows):
    print("Match_by_description")
    site_rows = exclude_oem_matches(site_rows, oem_dict)
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
    jobs_new_to_new = generate_jobs(site_rows, site_to_descs_preprocessed, oem_dict)
    jobs_new_to_old = generate_jobs(site_rows, old_site_to_descs_preprocessed, oem_dict)
    jobs_old_to_new = generate_jobs(old_site_rows, site_to_descs_preprocessed, oem_dict)
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
            results, scores = job #job.result()
            if str(item_id) not in desc_matches:
                desc_matches[str(item_id)] = {}
            #site_to_descs_preprocessed[site][results[0]]["Stock & Site"]
            #desc_matches[str(item_id)][site] = {"Matches": [site_to_descs_preprocessed[site][result]["Stock & Site"] for result in results], "Scores": [score for score in scores]}
            desc_matches[str(item_id)][site] = {"Matches": [all_site_to_descs_preprocessed[site][result]["Stock & Site"] for result in results], "Scores": [score for score in scores]}
    return desc_matches

def combine_desc_matches(matches1, matches2, n):
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
    all_matches = list(zip(m1["Matches"], m1["Scores"])) + list(zip(m2["Matches"], m2["Scores"]))
    all_matches = sorted(all_matches, key = lambda match: float(match[1]))
    all_matches = list(OrderedDict.fromkeys(all_matches)) #Remove duplicates
    result_matches = {"Matches": [], "Scores": []}
    for match in all_matches[:n]:
        result_matches["Matches"].append(match[0])
        result_matches["Scores"].append(match[1])
    return result_matches


def number(rows, start):
    num = start
    for row in rows:
        row["Item #"] = str(num)
        num += 1
    return rows, num

def find_row(old_item_ids_to_rows, item_id, match_site):
    if item_id in old_item_ids_to_rows:
        for row in old_item_ids_to_rows[item_id]:
            if row["Match Site"] == match_site:
                return row

def match_sites(site_rows, old_site_rows = {}, old_item_ids_to_rows = {}, matches_json="", exclude_unchanged = True):
    #num = 0
    #for site in site_rows:
    #    site_rows[site], num = number(site_rows[site], num)
    oem_dict = generate_oem_dict(site_rows, old_site_rows)
    sites = set(site_rows.keys()) | set(old_site_rows.keys())
    rows = base_rows_from(site_rows)
    old_rows = base_rows_from(old_site_rows)
    rows = rows + old_rows
    #rows = match_by_oem_code(oem_dict, rows)
    if matches_json and file_utils.file_exists(matches_json):
        desc_matches = file_utils.read_json(matches_json)
    else:
        desc_matches = match_by_description(oem_dict, site_rows, old_site_rows)
        if matches_json:
            file_utils.save_json(matches_json, desc_matches)
    final_rows = []
    for row in rows:
        row = copy.deepcopy(row)
        item_id = str(row["Stock & Site"])
        oem_code = str(row["OEM Code"])
        all_sites = set()
        if item_id in desc_matches:
            all_sites = all_sites | set(desc_matches[item_id])
        if oem_code in oem_dict:
            all_sites = all_sites | set(oem_dict[oem_code])
        for site in all_sites:
            if site == row["Site"]:
                continue
            site_row = copy.deepcopy(row)
            old_row = find_row(old_item_ids_to_rows, item_id, site)
            if old_row:
                site_row["Old Row"] = "Unchanged"
            else:
                site_row["Old Row"] = "No"
            site_row["Match Site"] = site
            if oem_code in oem_dict:
                if site in oem_dict[oem_code]:
                    site_row["OEM Code Match"] = oem_dict[oem_code][site]["Stock & Site"]
                    if old_row:
                        if old_row["OEM Code Match"] != site_row["OEM Code Match"]:
                            site_row["Old Row"] = "Yes"
            if item_id in desc_matches:
                if site in desc_matches[item_id]:
                    matches = desc_matches[item_id][site]
                    if old_row:
                        old_matches = {"Matches": [], "Scores": []}
                        old_match_set = set()
                        for i in range(10):
                            m = old_row["Description Match {}".format(str(i))]
                            c = old_row["Description Match {} Score".format(str(i))]
                            if not m:
                                break
                            old_match_set.add(m)
                            if m in matches["Matches"]:
                                continue
                            old_matches["Matches"].append(m)
                            old_matches["Scores"].append(c)
                        matches = top_n_matches(matches, old_matches, 10)
                        if set(matches["Matches"]) != old_match_set:
                            site_row["Old Row"] = "Yes"
                    for i, (match, score) in enumerate(zip(matches["Matches"], matches["Scores"])):
                        site_row["Description Match {}".format(str(i))] = match 
                        site_row["Description Match {} Score".format(str(i))] = score
            if not (site_row["Old Row"] == "Unchanged" and exclude_unchanged):
                final_rows.append(site_row)
    fieldnames = ["Site", "Match Site", "Stock & Site", "OEM Code", "Stock Code", "Description", "OEM Code Match", "Old Row"]
    for i in range(10):
        fieldnames.append("Description Match {}".format(str(i)))
        fieldnames.append("Description Match {} Score".format(str(i)))

    return (final_rows, fieldnames)

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
    if "Match Site" in dataframe.columns:
        ndf = dataframe[dataframe["Match Site"].map(str) == "-1"]
        if ndf.empty:
            #No new rows.
            return pandas.DataFrame()
        odf = dataframe[dataframe["Match Site"].map(str) != "-1"]
        n = ndf.iloc[0]
        ni = n.index[n!="-1"]
        ndf = ndf.loc[:, ni]
        o = odf.iloc[0]
        oi = o.index[o!="-1"]
        odf = odf.loc[:, oi]
        new_rows = ndf.to_dict("records")
        old_rows = odf.to_dict("records")
    else:
        new_rows = dataframe.to_dict("records")
        old_rows = []
    #print(ndf.head(n=10))
    #print(odf.head(n=10))
    site_rows = generate_site_to_rows_dict(new_rows)
    old_site_rows = generate_site_to_rows_dict(old_rows, old=True)
    old_item_ids_to_rows = generate_item_ids_to_rows(old_rows)
    matches_rows, _ = match_sites(site_rows, old_site_rows, old_item_ids_to_rows, matches_json)
    matches_df = pandas.DataFrame(matches_rows)
    return matches_df

def generate_site_to_rows_dict(rows, old=False):
    if old:
        item_ids = []
        new_rows = []
        for row in rows:
            row = copy.deepcopy(row)
            row["OEM Field"] = row["OEM Code"]
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
    if len(sys.argv) < 3:#4:
        print("""
        Script to match similar rows in data from different sites.

        Use: $ python oem_connecter.py sites.csv ouput.csv (optional)match_data.json

        Generating the description matches in match_data is by far the slowest part, so save it when expecting to re-use!
        """)
        sys.exit()
    #Use: $ python oem_connecter.py site1.csv site2.csv ouput.csv (optional)match_data.json
    #sqmo_file = sys.argv[1] #"FQMO.csv"
    #kalumbila_file = sys.argv[2] #"Kalumbila.csv"
    stime = time.time()
    sites_file = sys.argv[1]
    output_file = sys.argv[2]#[3] #"OEM_Match_Results.csv"
    matches_json = ""
    if len(sys.argv) == 4: #5:
        matches_json = sys.argv[3]#[4]
    #fqmo_rows = file_utils.read_csv(sqmo_file)
    #kalumbila_rows = file_utils.read_csv(kalumbila_file)
    sites_rows = file_utils.read_csv(sites_file)
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
    matches_df = match_sites_dataframe(df)
    print(matches_df.head(n=10))
    #result_rows = matches_df.to_dict("records")
    #print(result_rows[:10])
    #exclude_unchanged = False
    #result_rows, fieldnames = match_sites(site_rows, old_site_rows, old_item_ids_to_rows, matches_json, exclude_unchanged)
    #file_utils.save_csv(output_file, result_rows, fieldnames=fieldnames)
    etime = time.time()
    ttime = etime-stime
    print('Time = ', ttime, 's')
