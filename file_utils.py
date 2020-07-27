import os
import csv
import json

data_path = ""

def add_path(thing):
    return data_path + thing

def folder_exists(foldername):
    foldername = add_path(foldername)
    return os.path.isdir(foldername)

def file_exists(filename):
    filename = add_path(filename)
    return os.path.isfile(filename)

def mkdir(foldername):
    foldername = add_path(fldername)
    os.mkdir(foldername)

def save_json(filename, data, mode= "w"):
    filename = add_path(filename)
    with open(filename, mode, encoding="utf-8-sig") as f:
        json.dump(data, f)

def load_json(filename):
    filename = add_path(filename)
    with open(filename, encoding="utf-8-sig") as f:
        data = json.load(f)
    return data

def save_csv(filename, rows, mode = "w", fieldnames = []):
    filename = add_path(filename)
    exists = False
    if os.path.isfile(filename) and mode == "a":
       exists = True
    with open(filename, mode, encoding="utf-8-sig") as  fo:
        if fieldnames == []:
            w = csv.DictWriter(fo, fieldnames = list(rows[0].keys()))
        else:
            w = csv.DictWriter(fo, fieldnames = fieldnames)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(filename):
    filename = add_path(filename)
    rows = []
    with open(filename, encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def top_category_names():
    foldername = add_path("top_category_files")
    files = os.listdir(foldername)
    top_categories = []
    for f in files:
        tc = f.replace(".csv", "")
        if "~lock" not in tc:
            top_categories.append(tc)
    return top_categories
