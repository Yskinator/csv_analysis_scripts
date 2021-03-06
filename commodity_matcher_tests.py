"""Test cases for csv_scripts."""

import unittest
import copy
from commodity_matcher import match_commodities, add_commodities_to_stocks, map_preprocessed_to_original, order_fieldnames, unpivot_stocks

class AddCommoditiesToStocksTestCase(unittest.TestCase):
    """Test cases for add_commodities_to_stocks."""

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

    def test_output_contains_extra_columns(self):
        """Output should contain extra columns when topn > 1."""
        stock = [{"text": "circuit", "id": "1", "Brand": ""}]
        output = add_commodities_to_stocks(stock, topn=3)
        assert all([key in output[0][0] for key in ("Jaccard", "Jaccard 2", "Jaccard 3", "Commodity Code 2", "Commodity 3")])

class MatchCommoditiesTestCase(unittest.TestCase):
    """Test cases for match_commodities."""

    def test_output_contains_all_input_keys(self):
        """All the keys in the input dictionaries should also exist in the output dictionaries."""
        stock = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": ""}]
        for parallel in (True, False):
            output = match_commodities(stock, jaccard_threshold=0.3, topn=1, parallel=parallel)
            assert all([key in output[0] for key in stock[0]])

    def test_output_contains_extra_keys(self):
        """Output should contain keys Commodity, Commodity Code and Jaccard."""
        stock = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": ""}]
        for parallel in (True, False):
            output = match_commodities(stock, jaccard_threshold=0.3, topn=1, parallel=parallel)
            assert all([key in output[0] for key in ("Commodity", "Commodity Code", "Jaccard")])

    def test_output_contains_all_extra_keys(self):
        """Output should contain Commodity etc. for each result when multiple top results wanted."""
        stock = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": ""}]
        for parallel in (True, False):
            output = match_commodities(stock, jaccard_threshold=0.3, parallel=parallel, topn=2)
            assert all([key in output[0] for key in ("Commodity", "Commodity Code", "Jaccard", "Commodity 2", "Commodity Code 2", "Jaccard 2")])

class MapPreprocessedToOriginalTestCase(unittest.TestCase):
    """Test cases for map_preprocessed_to_original."""

    def test_output_contains_all_extra_keys(self):
        """Output should contain all the extra columns with Commodity, Commodity Code and Jaccard in stock_with_commodities."""
        original = [{"text": "circuit", "id": "1", "Brand": ""}]
        with_commodities = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": "", "Commodity": "Electric circuit", "Commodity Code": "200", "Jaccard": "0.99", "Commodity 2": "Track circuit", "Commodity Code 2": "400", "Jaccard 2": "0.5"}]*3
        output = map_preprocessed_to_original(original, with_commodities)
        assert all([key in output[0] for key in ("Commodity", "Commodity Code", "Jaccard", "Commodity 2", "Commodity Code 2", "Jaccard 2")])

class OrderFieldnamesTestCase(unittest.TestCase):
    """Test cases for order_fieldnames."""

    def test_fieldnames_contain_all_extra_keys_ordered(self):
        """Output fieldnames should contain all the extra column names with Commodity, Commodity Code and Jaccard in stock_with_commodities in the right order."""
        original = [{"text": "circuit", "id": "1", "Brand": ""}]
        with_commodities = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": "", "Commodity": "Electric circuit", "Commodity Code": "200", "Jaccard": "0.99", "Commodity 2": "Track circuit", "Commodity Code 2": "400", "Jaccard 2": "0.5"}]*3
        output = map_preprocessed_to_original(original, with_commodities)
        fieldnames = order_fieldnames(output)
        assert fieldnames == ["", "id", "language", "text", "Brand", "Commodity", "Commodity Code", "Jaccard", "Commodity 2", "Commodity Code 2", "Jaccard 2"]

    def test_fieldnames_equal_output_keys(self):
        """Output fieldnames should all be contained in output keys and vice versa."""
        original = [{"text": "circuit", "id": "1", "Brand": "", "language": ""}]
        with_commodities = [{"Description": "circuit", "id": "1", "Top Categories": "Electronic Components and Supplies", "Brands": "", "Commodity": "Electric circuit", "Commodity Code": "200", "Jaccard": "0.99", "Commodity 2": "Track circuit", "Commodity Code 2": "400", "Jaccard 2": "0.5"}]*2
        output = map_preprocessed_to_original(original, with_commodities)
        #print(['']+sorted(output[0][0].keys()))
        #print(sorted(output[1]))
        # Note: there's an extra '' in fieldnames
        # There's also a "language" field for some reason
        fieldnames = order_fieldnames(output)
        assert ['']+sorted(output[0].keys()) == sorted(fieldnames)

class UnpivotStocksTestCase(unittest.TestCase):
    """Test cases for unpivot_stocks."""

    def test_output_contains_match_number(self):
        """If the rows in the input stocks do not contain mulltiple commodities, return input unchanged except for an additional Match Number column."""
        stocks = [{"text": "circuit", "Commodity": "Electric circuit", "Commodity Code": "200", "Jaccard": "0.99"}]
        # The expression **stocks[0] includes all keys and values from dict stocks[0]
        stocks_with_match_num = [{**stocks[0], "Match Number": "1"}]
        assert unpivot_stocks(stocks) == stocks_with_match_num

    def test_multiple_commodities_on_multiple_rows(self):
        """If the rows in the input stocks contain mulltiple commodities, convert each row to multiple rows with appropriate Match Number."""
        stocks = [{"text": "circuit", "Commodity": "Electric circuit", "Commodity Code": "200", "Jaccard": "0.99", "Commodity 2": "Track circuit", "Commodity Code 2": "400", "Jaccard 2": "0.5"}]
        # The expression **stocks[0] includes all keys and values from dict stocks[0]
        stocks_with_match_num = [{"text": "circuit", "Commodity": "Electric circuit", "Commodity Code": "200", "Jaccard": "0.99", "Match Number": "1"},
                                                    {"text": "circuit", "Commodity": "Track circuit", "Commodity Code": "400", "Jaccard": "0.5", "Match Number": "2"}]
        assert unpivot_stocks(stocks) == stocks_with_match_num

if __name__ == "__main__":
    unittest.main()
