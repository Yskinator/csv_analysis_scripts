# csv_analysis_scripts
A compilation of ugly hacks designed to make sense of some absurdly large csv files.

Usage:

Install dependencies:

pip install -r requirements.txt


Plop in the required csvs:

combined_stock_master_withbrands.csv

unspsc_codes_3.csv

excluded_segments.csv


Generate the rest of the required csvs:
python constant_csv_generator.py


Run the script:
#level denotes the level to operate the initial matching at.
#num_to_check determines the amount of top categories that are checked first.
$ python csv_scripts.py filename.csv level[Segment, Family, Class] num_to_check[int]
