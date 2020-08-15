"""Test cases for csv_scripts."""

import unittest
import copy
from csv_scripts import match_commodities, add_commodities_to_stocks

class AddCommoditiesToStocksTestCase(unittest.TestCase):
    """Test cases for add_commodities_to_stocks."""

    def setUp(self):
        """Set up needed variables."""
        pass

    def tearDown(self):
        """Clean-up for next test case."""
        pass

    def test_should_not_affect_input(self):
        """Should not modify input list in place."""
        stock = [{"text": "circuit", "id": "1", "Brand": ""}]
        stock_copy = copy.deepcopy(stock)
        output = add_commodities_to_stocks(stock)
        assert stock == stock_copy

    def test_output_contains_all_input_keys(self):
        """All keys in input dictionaries should also exist in output dictionaries."""
        stock = [{"text": "circuit", "id": "1", "Brand": ""}]
        output = add_commodities_to_stocks(stock)
        assert all([key in output[0][0] for key in stock[0]])

class MatchCommoditiesTestCase(unittest.TestCase):
    """Test cases for match_commodities."""

    def setUp(self):
        """Set up needed variables."""
        pass

    def tearDown(self):
        """Clean-up for next test case."""
        pass

    def test_output_contains_all_input_keys(self):
        """All the keys in the input dictionaries should also exist in the output dictionaries."""
        stock = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": ""}]
        for parallel in (True, False):
            output = match_commodities(stock, jaccard_threshold=0.3, parallel=parallel)
            assert all([key in output[0] for key in stock[0]])

    def test_output_contains_extra_keys(self):
        """Output should contain keys Commodity, Commodity Code and Jaccard."""
        stock = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": ""}]
        for parallel in (True, False):
            output = match_commodities(stock, jaccard_threshold=0.3, parallel=parallel)
            assert all([key in output[0] for key in ("Commodity", "Commodity Code", "Jaccard")])

if __name__ == "__main__":
    unittest.main()
