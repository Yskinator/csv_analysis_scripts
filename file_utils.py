import os
import csv

def save_csv(filename, rows, mode = "w", fieldnames = []):
    exists = False
    if os.path.isfile(filename) and mode == "a":
       exists = True
    with open(filename, mode) as  fo:
        if fieldnames == []:
            w = csv.DictWriter(fo, fieldnames = list(rows[0].keys()))
        else:
            w = csv.DictWriter(fo, fieldnames = fieldnames)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(filename):
    rows = []
    with open(filename, encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def top_category_names():
    files = os.listdir("top_category_files")
    top_categories = []
    for f in files:
        tc = f.replace(".csv", "")
        if "~lock" not in tc:
            top_categories.append(tc)
    return top_categories
