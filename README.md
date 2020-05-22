# csv_analysis_scripts
A compilation of ugly hacks designed to make sense of some absurdly large csv files. These specific files. No general purpose scripts here.

Usage:
Install dependencies:
pip install -r requirements.txt
python -m spacy download en_vectors_web_lg

Plop in the required csvs:
combined_stock_master_withbrands.csv
unspsc_codes_3.csv

Run the script:
python csv_scripts.py
