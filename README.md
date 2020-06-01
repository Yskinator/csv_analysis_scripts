# csv_analysis_scripts
A compilation of ugly hacks designed to make sense of some absurdly large csv files.

Usage:

Install dependencies:

pip install -r requirements.txt


Plop in the required csvs:

combined_stock_master_withbrands.csv

unspsc_codes_3.csv

excluded_segments.csv


Create an environment variable LOCAL if not running on azure functions. This is needed because imports are handled differently there.

Linux:

in ~/.bashrc

export LOCAL="LOCAL"


Generate the rest of the required csvs:
python constant_csv_generator.py


Run the script:
#The number determines the amount of top categories that are checked first.
python csv_scripts.py combined_stock_master_withbrands.csv 50
