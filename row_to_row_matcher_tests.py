import unittest
import random
import string
import copy
import pandas

import row_to_row_matcher
from row_to_row_matcher import match_sites

def correct_input_2_rows():
    rows = []
    row = {}
    row["Site"] = "Site A"
    row["Stock & Site"] = "Unique ID 1"
    row["Stock Description"] = "Thingamajig"
    rows.append(row)
    row = {}
    row["Site"] = "Site B"
    row["Stock & Site"] = "Unique ID 2"
    row["Stock Description"] = "Thingamajig"
    rows.append(row)
    return rows

def missing_description_2_rows():
    rows = correct_input_2_rows()
    for row in rows:
        del row["Stock Description"]
    return rows

def correct_input_3_rows():
    rows = correct_input_2_rows()
    row = {}
    row["Site"] = "Site B"
    row["Stock & Site"] = "Unique ID 3"
    row["Stock Description"] = "Thingamajig The Second"
    rows.append(row)
    return rows

def one_empty_description_3_rows():
    rows = correct_input_3_rows()
    rows[2]["Stock Description"] = ""
    return rows

def one_None_description_3_rows():
    rows = correct_input_3_rows()
    rows[2]["Stock Description"] = None
    return rows

def correct_output_2_rows():
    rows = correct_input_2_rows()
    rows[0]["Stock Description"] = "Thingamajig The Third"
    rows[1]["Stock Description"] = "Thingamajig The Fourth"
    rows[0]["Stock & Site"] = "Unique ID 3"
    rows[1]["Stock & Site"] = "Unique ID 4"
    return match(rows)

def correct_output_3_rows_1_unchanged():
    rows = correct_output_2_rows()

    old_row = {'Site': 'Site A', 'Match Site': 'Site B', 'Stock & Site': 'Unique ID 1', 'Description': 'Thingamajig', 'Old Row': 'No', 'Match Description': 'Thingamajig', 'Match Stock & Site': 'Unique ID 2', 'Match Score': '1.0', 'Match Number': '0', 'Matching Row Count': '1'}
    rows.append(old_row)

    old_row = {'Site': 'Site A', 'Match Site': 'Site B', 'Stock & Site': 'Unique ID 1', 'Description': 'Thingamajig', 'Old Row': 'No', 'Match Description': 'Thingamajig The Fourth', 'Match Stock & Site': 'Unique ID 4', 'Match Score': '0.3333333333333333', 'Match Number': '1', 'Matching Row Count': 1}
    rows.append(old_row)

    return rows

def correct_input_2_rows_with_whitespace():
    rows = correct_input_2_rows()
    for row in rows:
        for key, val in row.items():
            row[key] = f"        {val}        "
    return rows

def correct_input_2_rows_only_1_site():
    rows = correct_input_2_rows()
    rows[1]["Site"] = "Site A"
    return rows

def match(rows, fieldnames = row_to_row_matcher.ALL_FIELDNAMES):
    df = pandas.DataFrame(rows, columns = fieldnames)
    df = df.fillna(value="-1")
    df_out = row_to_row_matcher.match_sites_dataframe(df)
    output_rows = df_out.to_dict("records")
    return sorted(output_rows, key = lambda row: row["Site"])

def match_2_inputs():
    rows = correct_input_2_rows()
    return match(rows)

def match_2_inputs_with_whitespace():
    rows = correct_input_2_rows_with_whitespace()
    return match(rows)

def match_2_inputs_only_1_site():
    rows = correct_input_2_rows_only_1_site()
    return match(rows)

def match_3_inputs():
    rows = correct_input_3_rows()
    return match(rows)

def match_2_inputs_and_outputs():
    rows_in = correct_input_2_rows()
    rows_out = correct_output_2_rows()
    rows = rows_in + rows_out
    return match(rows)

def match_2_inputs_and_3_outputs_1_unchanged():
    rows_in = correct_input_2_rows()
    rows_out = correct_output_3_rows_1_unchanged()
    rows = rows_in + rows_out
    return match(rows)

def match_1_empty_description_3_rows():
    rows = one_empty_description_3_rows()
    return match(rows)

def match_1_None_Description_3_rows():
    rows = one_None_description_3_rows()
    fieldnames = row_to_row_matcher.INPUT_FIELDNAMES
    df = pandas.DataFrame(rows, columns = fieldnames)
    df_out = row_to_row_matcher.match_sites_dataframe(df)
    output_rows = df_out.to_dict("records")
    return sorted(output_rows, key = lambda row: row["Site"])

def match_missing_description_2_rows():
    rows = missing_description_2_rows()
    fieldnames = row_to_row_matcher.INPUT_FIELDNAMES.remove("Stock Description")
    return match(rows, fieldnames=fieldnames)

def drop_old_rows(rows):
    results = []
    for row in rows:
        if row["Old Row"] != "Yes":
            results.append(row)
    return results


class IntegrationTestCase(unittest.TestCase):
    """Tests to see if the whole thing works."""

    @classmethod
    def setUpClass(cls):
        """Matching sites is slow - let's re-use results where we can."""
        super(IntegrationTestCase, cls).setUpClass()
        cls.correct_input_2_rows_output = match_2_inputs()
        cls.correct_input_2_rows_whitespace_output = match_2_inputs_with_whitespace()
        cls.correct_input_2_rows_only_1_site_output = match_2_inputs_only_1_site()
        cls.correct_input_3_rows_output = match_3_inputs()
        cls.correct_2_inputs_and_outputs_output = match_2_inputs_and_outputs()
        cls.correct_2_inputs_3_outputs_1_unchanged_output = match_2_inputs_and_3_outputs_1_unchanged()
        cls.one_empty_description_3_rows_output = match_1_empty_description_3_rows()
        cls.one_None_description_3_rows_output = match_1_None_Description_3_rows()
        cls.missing_description_2_rows_output = match_missing_description_2_rows()

    def assert_things_that_should_always_be_true(self, rows):
        self.assert_output_fieldnames_correct(rows)
        #self.assert_match_site_not_site(rows)
        self.assert_score_i_greater_than_score_i_plus_1(rows)

    def assert_score_i_greater_than_score_i_plus_1(self, rows):
        rows = sorted(rows, key = lambda row: row["Stock & Site"] + row["Match Site"] + row["Match Number"])
        prev_stock_n_site = "-1"
        prev_match_site = "-1"
        prev_score = "-1"
        for row in rows:
            if row["Stock & Site"] == prev_stock_n_site and row["Match Site"] == prev_match_site:
                self.assertGreaterEqual(float(prev_score), float(row["Match Score"]))
            prev_stock_n_site = row["Stock & Site"]
            prev_match_site = row["Match Site"]
            prev_score = row["Match Score"]

    def assert_persistent_columns_correct_2_rows(self, r1, r2):
        self.assertEqual(r1["Site"], "Site A")
        self.assertEqual(r2["Site"], "Site B")
        self.assertEqual(r1["Stock & Site"], "Unique ID 1")
        self.assertEqual(r2["Stock & Site"], "Unique ID 2")
        self.assertEqual(r1["Description"], "Thingamajig")
        self.assertEqual(r2["Description"], "Thingamajig")

    def assert_persistent_columns_exist(self, rows):
        for row in rows:
            self.assertIn("Site", row)
            self.assertIn("Stock & Site", row)
            self.assertIn("Description", row)

    def assert_match_columns_exist(self, rows):
        for row in rows:
            keys = row.keys()
            self.assertIn("Match Description", keys)
            self.assertIn("Match Stock & Site", keys)
            self.assertIn("Match Score", keys)
            self.assertIn("Match Site", keys)
            self.assertIn("Match Number", keys)
            self.assertIn("Matching Row Count", keys)

    def assert_output_fieldnames_correct(self, rows):
        fieldnames = row_to_row_matcher.OUTPUT_FIELDNAMES
        for row in rows:
            for fn in fieldnames:
                self.assertIn(fn, row)
            for key in row.keys():
                self.assertIn(key, fieldnames)

    def assert_new_columns_exist(self, rows):
        for row in rows:
            keys = row.keys()
            self.assertIn("Match Site", keys)
            self.assertIn("Old Row", keys)

    def assert_match_site_2_rows_correct(self, r1, r2):
        self.assertEqual("Site B", r1["Match Site"])
        self.assertEqual("Site A", r2["Match Site"])

    def assert_description_match_2_rows_correct(self, r1, r2):
        self.assertEqual("Thingamajig", r1["Match Description"])
        self.assertEqual("Thingamajig", r2["Match Description"])
        self.assertEqual("1.0", r1["Match Score"])
        self.assertEqual("1.0", r2["Match Score"])

    def assert_old_rows_no(self, rows):
        for row in rows:
            self.assertEqual("No", row["Old Row"])

    def assert_match_site_not_site(self,rows):
        for row in rows:
            self.assertNotEqual(row["Site"], row["Match Site"])

    def assert_description_match_3_rows_correct(self, r10, r11, r20, r30):
        self.assertEqual(r10["Match Description"], "Thingamajig")
        self.assertEqual(r10["Match Score"], "1.0")
        self.assertEqual(r11["Match Description"], "Thingamajig The Second")
        self.assertEqual(r11["Match Score"], "0.3333333333333333")
        self.assertEqual(r20["Match Description"], "Thingamajig")
        self.assertEqual(r20["Match Score"], "1.0")
        self.assertEqual(r30["Match Description"], "Thingamajig")
        self.assertEqual(r30["Match Score"], "0.3333333333333333")

    def assert_description_match_2_inputs_and_outputs_correct(self, r10, r11, r20, r21, r30, r31, r40, r41):
        self.assertEqual(r10["Match Description"], "Thingamajig")
        self.assertEqual(r10["Match Score"], "1.0")
        self.assertEqual(r11["Match Description"], "Thingamajig The Fourth")
        self.assertEqual(r11["Match Score"], "0.3333333333333333")
        self.assert_description_match_2_inputs_3_outputs_1_unchanged_correct(r20, r21, r30, r31, r40, r41)

    def assert_description_match_2_inputs_3_outputs_1_unchanged_correct(self, r20, r21, r30, r31, r40, r41):
        self.assertEqual(r20["Match Description"], "Thingamajig The Fourth")
        self.assertEqual(r20["Match Score"], "0.5")
        self.assertEqual(r21["Match Description"], "Thingamajig")
        self.assertEqual(r21["Match Score"], "0.3333333333333333")

        self.assertEqual(r30["Match Description"], "Thingamajig")
        self.assertEqual(r30["Match Score"], "1.0")
        self.assertEqual(r31["Match Description"], "Thingamajig The Third")
        self.assertEqual(r31["Match Score"], "0.3333333333333333")

        self.assertEqual(r40["Match Description"], "Thingamajig The Third")
        self.assertEqual(r40["Match Score"], "0.5")
        self.assertEqual(r41["Match Description"], "Thingamajig")
        self.assertEqual(r41["Match Score"], "0.3333333333333333")


    def assert_empty_descriptions_should_give_poor_matches(self, rows):
        """Score for empty descriptino matches should be 0"""
        for row in rows:
            if not row["Description"]:
                self.assertEqual(row["Match Score"], "0.0")
                #Description matches that match to current row
                for other_row in rows:
                    if other_row != row and other_row["Match Site"] == row["Site"]:
                        match = other_row["Match Stock & Site"]
                        score = other_row["Match Score"]
                        if match == row["Stock & Site"]:
                            self.assertEqual(score, "0.0")

    def test_2_rows_persistent_columns_exist(self):
        rows = self.correct_input_2_rows_output
        self.assert_persistent_columns_exist(rows)

    def test_2_rows_persistent_columns_correct(self):
        rows = self.correct_input_2_rows_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_persistent_columns_correct_2_rows(r1, r2)

    def test_2_rows_match_columns_exist(self):
        rows = self.correct_input_2_rows_output
        self.assert_match_columns_exist(rows)

    def test_2_rows_new_columns_exist(self):
        rows = self.correct_input_2_rows_output
        self.assert_new_columns_exist(rows)

    def test_2_rows_match_site_correct(self):
        rows = self.correct_input_2_rows_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_match_site_2_rows_correct(r1, r2)

    def test_2_rows_description_match_correct(self):
        rows = self.correct_input_2_rows_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_2_rows_old_row_correct(self):
        rows = self.correct_input_2_rows_output
        self.assert_old_rows_no(rows)

    def test_2_rows_whitespace_persistent_columns_exist(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_persistent_columns_exist(rows)

    def test_2_rows_whitespace_persistent_columns_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_persistent_columns_correct_2_rows(r1, r2)

    def test_2_rows_whitespace_match_columns_exist(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_match_columns_exist(rows)

    def test_2_rows_whitespace_new_columns_exist(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_new_columns_exist(rows)

    def test_2_rows_whitespace_match_site_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_match_site_2_rows_correct(r1, r2)

    def test_2_rows_whitespace_description_match_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_2_rows_whitespace_old_row_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_old_rows_no(rows)

    def test_2_rows_only_1_site_empty(self):
        rows = self.correct_input_2_rows_only_1_site_output
        self.assertEqual([], rows)

    def test_3_rows_correct_columns(self):
        rows = self.correct_input_3_rows_output
        self.assert_output_fieldnames_correct(rows)

    #def test_3_rows_match_site_not_site(self):
    #    rows = self.correct_input_3_rows_output
    #    self.assert_match_site_not_site(rows)

    def test_3_rows_description_matches_correct(self):
        rows = self.correct_input_3_rows_output
        self.assert_description_match_3_rows_correct(rows[0], rows[1], rows[2], rows[3])

    def test_2_inputs_and_outputs_things_that_should_always_be_true(self):
        rows = self.correct_2_inputs_and_outputs_output
        self.assert_things_that_should_always_be_true(rows)

    def test_2_inputs_and_outputs_description_matches_correct(self):
        rows = self.correct_2_inputs_and_outputs_output
        rows = drop_old_rows(rows)
        self.assertEqual(len(rows), 8)
        r10, r11, r20, r21, r30, r31, r40, r41 = rows
        self.assert_description_match_2_inputs_and_outputs_correct(r10, r11, r20, r21, r30, r31, r40, r41)

    def test_2_inputs_3_outputs_1_unchanged_things_that_should_always_be_true(self):
        rows = self.correct_2_inputs_3_outputs_1_unchanged_output
        self.assert_things_that_should_always_be_true(rows)

    def test_2_inputs_3_outputs_1_unchanged_description_matches_correct(self):
        rows = self.correct_2_inputs_3_outputs_1_unchanged_output
        rows = drop_old_rows(rows)
        self.assertEqual(len(rows), 6)
        r20, r21, r30, r31, r40, r41 = rows
        self.assert_description_match_2_inputs_3_outputs_1_unchanged_correct(r20, r21, r30, r31, r40, r41)

    def test_1_empty_description_3_rows_things_that_should_always_be_true(self):
        rows = self.one_empty_description_3_rows_output
        self.assert_things_that_should_always_be_true(rows)

    def test_1_empty_description_3_rows_empty_description_gives_poor_matches(self):
        rows = self.one_empty_description_3_rows_output
        self.assert_empty_descriptions_should_give_poor_matches(rows)

    def test_1_empty_description_3_rows_other_descriptions_match_normally(self):
        rows = self.one_empty_description_3_rows_output
        r1, _, r2, _ = rows
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_1_None_description_3_rows_things_that_should_always_be_true(self):
        rows = self.one_None_description_3_rows_output
        self.assert_things_that_should_always_be_true(rows)

    def test_1_None_description_3_rows_None_description_gives_poor_matches(self):
        rows = self.one_None_description_3_rows_output
        self.assert_empty_descriptions_should_give_poor_matches(rows)

    def test_1_None_description_3_rows_other_descriptions_match_normally(self):
        rows = self.one_None_description_3_rows_output
        r1, _, r2, _ = rows
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_missing_description_2_rows_things_that_should_always_be_true(self):
        rows = self.missing_description_2_rows_output
        self.assert_things_that_should_always_be_true(rows)

    #TODO: Multiple sites, more missing columns, etc


class TopNMatchesUnitTest(unittest.TestCase):
    """Test if the top_n_matches function works."""

    def n_sets_of_matches(self, n):
        matches = []
        for _ in range(n):
            matches.append(self.random_matches(random.randint(1, 40)))
        return matches

    def random_matches(self, n):
        matches = {"Matches": [], "Scores": [], "Stock & Site": []}
        for _ in range(n):
            match = self.random_match()
            matches["Matches"].append(match[0])
            matches["Scores"].append(match[1])
            matches["Stock & Site"].append(match[2])
        return matches

    def random_match(self):
        return ("".join(random.choices(string.ascii_lowercase, k=10)), random.uniform(0,1), {"".join(random.choices(string.ascii_lowercase, k=10)) for _ in range(random.randint(1,3))})

    def duplicate_match(self, matches):
        matches = copy.deepcopy(matches)
        i = random.randint(0, len(matches["Matches"])-1)
        matches["Matches"].append(matches["Matches"][i])
        matches["Scores"].append(matches["Scores"][i])
        matches["Stock & Site"].append(matches["Stock & Site"][i])
        return matches

    def duplicate_match_diff_stock_n_site(self, matches):
        matches = copy.deepcopy(matches)
        matches = self.duplicate_match(matches)
        for _ in range(random.randint(1,3)):
            matches["Stock & Site"][-1].add("".join(random.choices(string.ascii_lowercase, k=10)))
        return matches

    def copy_match_m1_to_m2(self, m1, m2):
        m2 = copy.deepcopy(m2)
        m2["Matches"].append(m1["Matches"][0])
        m2["Scores"].append(m1["Scores"][0])
        m2["Stock & Site"].append(m1["Stock & Site"][0])
        return m2

    def assert_is_n_matches(self, matches, n):
        self.assertEqual(len(matches["Matches"]), n)
        self.assertEqual(len(matches["Scores"]), n)
        self.assertEqual(len(matches["Stock & Site"]), n)

    def assert_each_match_has_at_least_one_stock_n_site(self, matches):
        for rows in matches["Stock & Site"]:
            self.assertTrue(len(rows) >= 1)

    def assert_has_no_duplicate_matches(self, matches):
        match_tuples = []
        for i in range(len(matches["Matches"])):
            match_tuples.append((matches["Matches"][i], matches["Scores"][i], matches["Stock & Site"][i]))
        i = 0
        for match in match_tuples:
            for match2 in match_tuples:
                if match == match2:
                    i += 1
            self.assertEqual(i, 1)
            i = 0

    def test_random_matches(self):
        for _ in range(10):
            n = random.randint(1, 40)
            matches = self.random_matches(n)
            self.assert_is_n_matches(matches, n)
            self.assert_each_match_has_at_least_one_stock_n_site(matches)

    def test_top_n_matches_returns_up_to_n_matches(self):
        matches = zip(self.n_sets_of_matches(10), self.n_sets_of_matches(10))
        for (m1, m2) in matches:
            n = random.randint(1, 40)
            matches = row_to_row_matcher.top_n_matches(m1, m2, n)
            if n < len(m1["Matches"]) + len(m2["Matches"]):
                self.assert_is_n_matches(matches, n)
            else:
                self.assert_is_n_matches(matches, len(m1["Matches"]) + len(m2["Matches"]))

    def test_top_n_matches_returns_no_duplicate_matches(self):
        #Duplicates caused by same match appearing twice in same set of matches
        matches = zip(self.n_sets_of_matches(10), self.n_sets_of_matches(10))
        for (m1, m2) in matches:
            n = random.randint(1, 40)
            m1 = self.duplicate_match(m1)
            matches = row_to_row_matcher.top_n_matches(m1, m2, n)
            self.assert_has_no_duplicate_matches(matches)

        #Duplicates caused by changing the rows that match to a match description
        matches = zip(self.n_sets_of_matches(10), self.n_sets_of_matches(10))
        for (m1, m2) in matches:
            n = random.randint(1, 40)
            m1 = self.duplicate_match_diff_stock_n_site(m1)
            matches = row_to_row_matcher.top_n_matches(m1, m2, n)
            self.assert_has_no_duplicate_matches(matches)

        #Duplicates caused by same match appearing in both sets of matches
        matches = zip(self.n_sets_of_matches(10), self.n_sets_of_matches(10))
        for (m1, m2) in matches:
            n = random.randint(1, 40)
            m2 = self.copy_match_m1_to_m2(m1, m2)
            matches = row_to_row_matcher.top_n_matches(m1, m2, n)
            self.assert_has_no_duplicate_matches(matches)

class MatchSitesTestCase(unittest.TestCase):
    """Tests for match_sites."""

    def test_returns_empty_list_if_empty(self):
        """If input dictionary is empty, return an empty list."""
        assert match_sites({}) == []

    def test_every_input_row_has_at_least_one_match(self):
        """All input rows should have at least one match in the output."""
        rows = [{"Stock & Site": "1", "Stock Code": "A", "Stock Description": "Thing"}]
        assert len(match_sites({"1": rows, "2": rows})) >= 2
        assert len(match_sites({"1": rows, "2": rows, "3": rows})) >= 3

    def test_all_matches_should_contain_keys(self):
        """All output matches should contain the keys 'Match Site', 'Old Row', 'Match Description', 'Match Stock & Site', 'Match Score', 'Match Number' and 'Matching Row Count'"""
        required_keys = ["Match Site", "Old Row", "Match Description", "Match Stock & Site", "Match Score", "Match Number", "Matching Row Count"]
        rows = [{"Stock & Site": "1", "Stock Code": "A", "Stock Description": "Thing"}]
        output = match_sites({"1": rows, "2": rows, "3": rows})
        for match in output:
            assert all([key in match for key in required_keys])

    def test_identical_rows_should_match_perfectly(self):
        """Identical rows should match each other with a match score of 1.0."""
        rows = [{"Stock & Site": "1", "Stock Code": "A", "Stock Description": "Thing"}]
        output = match_sites({"1": rows, "2": rows})
        expected_output = [{'Stock & Site': '1', 'Site': '1', 'Description': 'Thing', 'Match Site': '2', 'Old Row': 'No', 'Match Description': 'Thing', 'Match Stock & Site': '1', 'Match Score': '1.0', 'Match Number': '0', 'Matching Row Count': '1'}, {'Stock & Site': '1', 'Site': '2', 'Description': 'Thing', 'Match Site': '1', 'Old Row': 'No', 'Match Description': 'Thing', 'Match Stock & Site': '1', 'Match Score': '1.0', 'Match Number': '0', 'Matching Row Count': '1'}]
        for row in expected_output:
            assert row in output

    def test_bad_match_should_score_zero(self):
        """If row has no valid matches, best match score should be 0.0."""
        rows = [{"Stock & Site": "1", "Stock Code": "A", "Stock Description": "Thing"}]
        rows2 = [{"Stock & Site": "2", "Stock Code": "B", "Stock Description": "Some"}]
        output = match_sites({"1": rows, "2": rows2})
        for row in output:
            assert row["Match Score"] == "0.0"

    # NOTE: matches_json functionality testing is currently left unimplemented. To facilitate testing, the functionality should be rewritten so that file reads and writes are done outside of match_sites

    def test_does_not_return_old_rows_if_exclude_unchanged_true(self):
        """If exclude_unchanged == True, and all rows are old, return an empty list."""
        # Note that currently if only some matches are old, exclude_unchanged is ignored for that site, all old matches are kept and marked "Old Row": "Yes" rather than "Unchanged"
        rows = [{"Stock & Site": "1", "Stock Code": "A", "Stock Description": "Thing"}]
        rows2 = [{"Stock & Site": "2", "Stock Code": "B", "Stock Description": "Some"}]
        output = match_sites({"1": rows, "2": rows2})
        old_item_ids_to_rows = {output[0]["Stock & Site"]: [output[0]], output[1]["Stock & Site"]: [output[1]]}
        assert match_sites({"1": rows, "2": rows2}, old_item_ids_to_rows=old_item_ids_to_rows, exclude_unchanged=True) == []

    def test_rows_marked_unchanged_if_exclude_unchanged_false(self):
        """If exclude_unchanged == False, and all rows are old, return them with "Old Row": "Unchanged"."""
        rows = [{"Stock & Site": "1", "Stock Code": "A", "Stock Description": "Thing"}]
        rows2 = [{"Stock & Site": "2", "Stock Code": "B", "Stock Description": "Some"}]
        output = match_sites({"1": rows, "2": rows2})
        old_item_ids_to_rows = {output[0]["Stock & Site"]: [output[0]], output[1]["Stock & Site"]: [output[1]]}
        new_output = match_sites({"1": rows, "2": rows2}, old_item_ids_to_rows=old_item_ids_to_rows, exclude_unchanged=False)
        for row in new_output:
            assert  row["Old Row"] == "Unchanged"

    def test_if_some_old_and_some_new_old_row_should_be_yes_or_no(self):
        """If some rows are old and some new, and exclude_unchanged == True, all rows should have "Old Row": "Yes" or "No" but not "Unchanged"."""
        rows = [{"Stock & Site": "1", "Stock Code": "A", "Stock Description": "Thing"}]
        rows2 = [{"Stock & Site": "2", "Stock Code": "B", "Stock Description": "Some"}]
        output = match_sites({"1": rows, "2": rows2})
        old_item_ids_to_rows = {output[0]["Stock & Site"]: [output[0]], output[1]["Stock & Site"]: [output[1]]}
        rows2.append({"Stock & Site": "3", "Stock Code": "C", "Stock Description": "Else"})
        new_output = match_sites({"1": rows, "2": rows2} , old_item_ids_to_rows=old_item_ids_to_rows)
        assert any([row["Old Row"] == "Yes" for row in new_output])
        assert any([row["Old Row"] == "No" for row in new_output])
        for row in new_output:
            assert row["Old Row"] == "Yes" or row["Old Row"] == "No"

    # UNTESTED: if some rows are old and some new, all old rows are preserved. Note that as far as I can tell sometimes old rows might appear twice, once with "Old Row": "Yes" as a preserved row,
    # and once with "Old Row": "No" as a "new" match (this happens if no better match was found.)

if __name__ == "__main__":
    unittest.main()
    #import file_utils
    #file_utils.save_csv("test_out.csv", match_1_None_Description_3_rows(), fieldnames=row_to_row_matcher.OUTPUT_FIELDNAMES)
