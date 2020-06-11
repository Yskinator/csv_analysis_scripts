import file_utils
from collections import defaultdict

def generate_dict(fqmo, kalumbila):
    oem_dict = {}
    oem_dict = update_oem_dict("FQMO", oem_dict, fqmo)
    oem_dict = update_oem_dict("Kalumbila", oem_dict, kalumbila)
    return oem_dict

def update_oem_dict(site, oem_dict, rows):
    for row in rows:
        oem_code = row["OEM Field"]
        if oem_code in oem_dict:
            single_oem = oem_dict[oem_code]
        else:
            single_oem = {}
        single_oem[site] = {"Description": row["Stock Description"], "Code": row["Stock Code"]}
        oem_dict[oem_code] = single_oem
    return oem_dict

def write_results_file(oem_dict, output_file):
    rows = []
    fieldnames = ["Site", "Item #", "OEM Code", "Stock Code", "Appended", "Kalumbila", "FQMO"]
    item_num = 0
    for oem_code in oem_dict:
        site_to_num = defaultdict(str)
        oem_data = oem_dict[oem_code]
        for site in oem_data:
            site_to_num[site] = str(item_num)
            item_num += 1
        for site in oem_data:
            row = {}
            row["Site"] = site
            row["Item #"] = site_to_num[site]
            row["OEM Code"] = oem_code
            row["Stock Code"] = oem_data[site]["Code"]
            desc = oem_data[site]["Description"]
            row["Appended"] = "{} {}".format(oem_code, desc)
            for site in oem_data:
                row[site] = site_to_num[site]
            rows.append(row)
    file_utils.save_csv(output_file, rows, fieldnames = fieldnames)



def match_oems():
    fqmo_file = "FQMO.csv"
    kalumbila_file = "Kalumbila.csv"
    fqmo_rows = file_utils.read_csv(fqmo_file)
    kalumbila_rows = file_utils.read_csv(kalumbila_file)
    oem_dict = generate_dict(fqmo_rows, kalumbila_rows)
    write_results_file(oem_dict, "OEM_Match_Results.csv")

if __name__=="__main__":
    match_oems()
