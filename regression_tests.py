"""Regression tests for analysis scripts."""

import unittest
#from utilities import read_csv
import commodity_matcher
from file_utils import read_csv
#from . import csv_scripts
import sys

class RegressionTestCase(unittest.TestCase):
    """Test for regressions introduced by new code."""

    def test_regression(self):
        """Rerun code on regression_test_stock_master.csv and make sure the results match."""
        #print(sys.path)
        stock_master = read_csv("regression_test_stock_master.csv")
        rows, fieldnames = commodity_matcher.add_commodities_to_stocks(stock_master[:100])
        all_matched = True
        for i, row in enumerate(rows):
            if not row['Commodity'] == stock_master[i]['Commodity']:
                print("Did not match, row "+str(i)+", "+row['text'])
                print("New: '"+row['Commodity']+"' vs. Original: '"+stock_master[i]['Commodity']+"'")
                all_matched = False
        assert(len(rows) == 100)
        assert(sorted(rows[0].keys()) == sorted(fieldnames))
        assert(sorted(fieldnames) == sorted(stock_master[0].keys()))
        if not all_matched:
            print("WARNING: all of the rows did not match. If the above results look fine, you may want to update regression_test_stock_master.csv.")

if __name__ == "__main__":
    unittest.main()
