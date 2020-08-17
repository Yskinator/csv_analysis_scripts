"""Tests for top_category_matcher."""

import unittest

import file_utils
from top_category_matcher import excluded_segments, excluded_top_categories, non_excluded_top_categories

class ExcludedSegmentsTestCase(unittest.TestCase):
    """Test excluded_segments"""

    def setUp(self):
        """Set up needed variables."""
        pass

    def tearDown(self):
        """Tear down variables for next pass."""
        pass

    def test_returns_empty_if_none_excluded(self):
        """Should return an empty list if none are excluded."""
        input_segments = [{"Segment Name": "nosuch", "Remove?": ""}, {"Segment Name": "hello world", "Remove?": ""}]
        output = excluded_segments(input_segments)
        assert output == []

    def test_returns_all_if_all_excluded(self):
        """Should return all input Segment Names if all input segments are excluded."""
        input_segments = [{"Segment Name": "nosuch", "Remove?": "YES"}, {"Segment Name": "hello world", "Remove?": "YES"}]
        output = excluded_segments(input_segments)
        assert len(output) == 2
        assert all([segment in ["nosuch", "hello world"] for segment in output])

class ExcludedTopCategoriesTestCase(unittest.TestCase):
    """Tests for excluded_top_categories and non_excluded_top_categories."""

    def test_exhaustive(self):
        """All top categories should be included in either excluded or non-excluded top categories."""
        excluded = excluded_top_categories()
        non_excluded = non_excluded_top_categories()
        top_cat = file_utils.top_category_names()
        assert all([cat in excluded+non_excluded for cat in top_cat])

    def test_empty_intersection(self):
        """Excluded and non-excluded top categories should not have any categories in common."""
        excluded = excluded_top_categories()
        non_excluded = non_excluded_top_categories()
        assert all([cat not in excluded for cat in non_excluded])

if __name__ == "__main__":
    unittest.main()
