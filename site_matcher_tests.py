import unittest
import site_matcher
import pandas

def correct_input_2_rows():
    rows = []
    row = {}
    row["Site"] = "Site A"
    row["Stock Code"] = "123"
    row["Stock & Site"] = "Unique ID 1"
    row["OEM Field"] = ""
    row["Stock Description"] = "Thingamajig"
    rows.append(row)
    row = {}
    row["Site"] = "Site B"
    row["Stock Code"] = "456"
    row["Stock & Site"] = "Unique ID 2"
    row["OEM Field"] = ""
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
    row["Stock Code"] = "789"
    row["Stock & Site"] = "Unique ID 3"
    row["OEM Field"] = ""
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

def correct_input_2_rows_oem_match():
    rows = correct_input_2_rows()
    rows[0]["OEM Field"] = "Match made in heaven"
    rows[1]["OEM Field"] = "Match made in heaven"
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
    old_row = {'Site': 'Site A', 'Match Site': 'Site B', 'Stock & Site': 'Unique ID 1', 'OEM Code': '', 'Stock Code': '123', 'Description': 'Thingamajig', 'OEM Code Match': '', 'Old Row': 'No', 'Description Match 0': 'Thingamajig', 'Description Match 0 Score': '1.0', 'Description Match 1': 'Thingamajig The Fourth', 'Description Match 1 Score': '0.3333333333333333', 'Description Match 2': '', 'Description Match 2 Score': '', 'Description Match 3': '', 'Description Match 3 Score': '', 'Description Match 4': '', 'Description Match 4 Score': '', 'Description Match 5': '', 'Description Match 5 Score': '', 'Description Match 6': '', 'Description Match 6 Score': '', 'Description Match 7': '', 'Description Match 7 Score': '', 'Description Match 8': '', 'Description Match 8 Score': '', 'Description Match 9': '', 'Description Match 9 Score': ''}
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

def match(rows, fieldnames = site_matcher.all_fieldnames()):
    df = pandas.DataFrame(rows, columns = fieldnames)
    df = df.fillna(value="-1")
    df_out = site_matcher.match_sites_dataframe(df)
    output_rows = df_out.to_dict("records")
    return sorted(output_rows, key = lambda row: row["Site"])

def match_2_correct_inputs():
    rows = correct_input_2_rows()
    return match(rows)

def match_2_correct_inputs_with_whitespace():
    rows = correct_input_2_rows_with_whitespace()
    return match(rows)

def match_2_correct_inputs_only_1_site():
    rows = correct_input_2_rows_only_1_site()
    return match(rows)

def match_3_correct_inputs():
    rows = correct_input_3_rows()
    return match(rows)

def match_2_correct_inputs_and_outputs():
    rows_in = correct_input_2_rows()
    rows_out = correct_output_2_rows()
    rows = rows_in + rows_out
    return match(rows)

def match_2_correct_inputs_and_3_outputs_1_unchanged():
    rows_in = correct_input_2_rows()
    rows_out = correct_output_3_rows_1_unchanged()
    rows = rows_in + rows_out
    return match(rows)

def match_2_correct_inputs_oem_match():
    rows = correct_input_2_rows_oem_match()
    return match(rows)

def match_1_empty_description_3_rows():
    rows = one_empty_description_3_rows()
    return match(rows)

def match_1_None_Description_3_rows():
    rows = one_None_description_3_rows()
    fieldnames = site_matcher.input_fieldnames()
    df = pandas.DataFrame(rows, columns = fieldnames)
    df_out = site_matcher.match_sites_dataframe(df)
    output_rows = df_out.to_dict("records")
    return sorted(output_rows, key = lambda row: row["Site"])

def match_missing_description_2_rows():
    rows = missing_description_2_rows()
    fieldnames = site_matcher.input_fieldnames().remove("Stock Description")
    return match(rows, fieldnames=fieldnames)


class IntegrationTestCase(unittest.TestCase):
    """Tests to see if the whole thing works."""

    @classmethod
    def setUpClass(cls):
        """Matching sites is slow - let's re-use results where we can."""
        super(IntegrationTestCase, cls).setUpClass()
        cls.correct_input_2_rows_output = match_2_correct_inputs()
        cls.correct_input_2_rows_whitespace_output = match_2_correct_inputs_with_whitespace()
        cls.correct_input_2_rows_only_1_site_output = match_2_correct_inputs_only_1_site()
        cls.correct_input_3_rows_output = match_3_correct_inputs()
        cls.correct_2_inputs_and_outputs_output = match_2_correct_inputs_and_outputs()
        cls.correct_2_inputs_3_outputs_1_unchanged_output = match_2_correct_inputs_and_3_outputs_1_unchanged()
        cls.correct_2_inputs_oem_match_output = match_2_correct_inputs_oem_match()
        cls.one_empty_description_3_rows_output = match_1_empty_description_3_rows()
        cls.one_None_description_3_rows_output = match_1_None_Description_3_rows()
        cls.missing_description_2_rows_output = match_missing_description_2_rows()

    def assert_things_that_should_always_be_true(self, rows):
        self.assert_output_fieldnames_correct(rows)
        #self.assert_match_site_not_site(rows)
        self.assert_score_i_greater_than_score_i_plus_1(rows)

    def assert_score_i_greater_than_score_i_plus_1(self, rows):
        for row in rows:
            for i in range(9):
                score_i = f"Description Match {i} Score"
                score_i_plus_1 = f"Description Match {i+1} Score"
                if not row[score_i_plus_1]:
                    break
                self.assertTrue(row[score_i] > row[score_i_plus_1])

    def assert_persistent_columns_correct_2_rows(self, r1, r2):
        self.assertEqual(r1["Site"], "Site A")
        self.assertEqual(r2["Site"], "Site B")
        self.assertEqual(r1["Stock & Site"], "Unique ID 1")
        self.assertEqual(r2["Stock & Site"], "Unique ID 2")
        self.assertEqual(r1["Stock Code"], "123")
        self.assertEqual(r2["Stock Code"], "456")
        self.assertEqual(r1["OEM Code"], "")
        self.assertEqual(r2["OEM Code"], "")
        self.assertEqual(r1["Description"], "Thingamajig")
        self.assertEqual(r2["Description"], "Thingamajig")

    def assert_persistent_columns_exist(self, rows):
        for row in rows:
            self.assertIn("Site", row)
            self.assertIn("Stock & Site", row)
            self.assertIn("Stock Code", row)
            self.assertIn("OEM Code", row)
            self.assertIn("Description", row)

    def assert_10_match_columns(self, rows):
        for row in rows:
            keys = row.keys()
            for i in range(10):
                match_column = f"Description Match {i}"
                score_column = match_column + " Score"
                self.assertIn(match_column, keys)
                self.assertIn(score_column, keys)

    def assert_output_fieldnames_correct(self, rows):
        fieldnames = site_matcher.output_fieldnames()
        for row in rows:
            for fn in fieldnames:
                self.assertIn(fn, row)
            for key in row.keys():
                self.assertIn(key, fieldnames)

    def assert_new_columns_exist(self, rows):
        for row in rows:
            keys = row.keys()
            self.assertIn("Match Site", keys)
            self.assertIn("OEM Code Match", keys)
            self.assertIn("Old Row", keys)

    def assert_match_site_2_rows_correct(self, r1, r2):
        self.assertEqual("Site B", r1["Match Site"])
        self.assertEqual("Site A", r2["Match Site"])

    def assert_oem_match_2_rows_correct(self, r1, r2):
        self.assertEqual("", r1["OEM Code Match"])
        self.assertEqual("", r2["OEM Code Match"])

    def assert_description_match_2_rows_correct(self, r1, r2):
        self.assertEqual("Thingamajig", r1["Description Match 0"])
        self.assertEqual("Thingamajig", r2["Description Match 0"])
        self.assertEqual("1.0", r1["Description Match 0 Score"])
        self.assertEqual("1.0", r2["Description Match 0 Score"])

    def assert_extra_match_columns_empty(self, rows, start_index):
        for row in rows:
            for i in range(start_index, 10):
                match_column = f"Description Match {i}"
                score_column = match_column + " Score"
                self.assertEqual("", row[match_column])
                self.assertEqual("", row[score_column])

    def assert_old_rows_no(self, rows):
        for row in rows:
            self.assertEqual("No", row["Old Row"])

    def assert_match_site_not_site(self,rows):
        for row in rows:
            self.assertNotEqual(row["Site"], row["Match Site"])

    def assert_no_oem_code_matches(self, rows):
        for row in rows:
            self.assertEqual("", row["OEM Code Match"])

    def assert_description_match_3_rows_correct(self, r1, r2, r3):
        self.assertEqual(r1["Description Match 0"], "Thingamajig")
        self.assertEqual(r1["Description Match 0 Score"], "1.0")
        self.assertEqual(r1["Description Match 1"], "Thingamajig The Second")
        self.assertEqual(r1["Description Match 1 Score"], "0.3333333333333333")
        self.assertEqual(r2["Description Match 0"], "Thingamajig")
        self.assertEqual(r3["Description Match 0"], "Thingamajig")
        self.assertEqual(r2["Description Match 0 Score"], "1.0")
        self.assertEqual(r3["Description Match 0 Score"], "0.3333333333333333")
        self.assert_extra_match_columns_empty([r1], 2)
        self.assert_extra_match_columns_empty([r2, r3], 1)

    def assert_description_match_2_correct_inputs_and_outputs_correct(self, r1, r2, r3, r4):
        self.assertEqual(r1["Description Match 0"], "Thingamajig")
        self.assertEqual(r1["Description Match 0 Score"], "1.0")
        self.assertIn(r1["Description Match 1"], ["Thingamajig The Second", "Thingamajig The Fourth"])
        self.assertEqual(r1["Description Match 1 Score"], "0.3333333333333333")
        self.assert_description_match_2_inputs_3_outputs_1_unchanged_correct(r2, r3, r4)

    def assert_description_match_2_inputs_3_outputs_1_unchanged_correct(self, r2, r3, r4):
        self.assertEqual(r2["Description Match 0"], "Thingamajig The Fourth")
        self.assertEqual(r2["Description Match 0 Score"], "0.5")
        self.assertIn(r2["Description Match 1"], ["Thingamajig", "Thingamajig The Fourth"])
        self.assertEqual(r2["Description Match 1 Score"], "0.3333333333333333")

        self.assertEqual(r3["Description Match 0"], "Thingamajig")
        self.assertEqual(r3["Description Match 0 Score"], "1.0")
        self.assertIn(r3["Description Match 1"], ["Thingamajig The Third", "Thingamajig The Fourth"])
        self.assertEqual(r3["Description Match 1 Score"], "0.3333333333333333")

        self.assertEqual(r4["Description Match 0"], "Thingamajig The Third")
        self.assertEqual(r4["Description Match 0 Score"], "0.5")
        self.assertIn(r4["Description Match 1"], ["Thingamajig", "Thingamajig The Third"])
        self.assertEqual(r4["Description Match 1 Score"], "0.3333333333333333")

    def assert_oem_match_2_inputs_oem_match_correct(self, r1, r2):
        self.assertEqual(r1["OEM Code Match"], "Unique ID 2")
        self.assertEqual(r2["OEM Code Match"], "Unique ID 1")

    def assert_empty_descriptions_should_give_poor_matches(self, rows):
        """Score for empty descriptino matches should be 0"""
        for row in rows:
            if not row["Description"]:
                #Row's description matches
                for i in range(10):
                    column = f"Description Match {i} Score"
                    if row[column]:
                        self.assertEqual(row[column], "0.0")
                #Description matches that match to current row
                for other_row in rows:
                    if other_row != row and other_row["Match Site"] == row["Site"]:
                        for i in range(10):
                            match = other_row[f"Description Match {i}"]
                            score = other_row[f"Description Match {i} Score"]
                            if match == row["Stock & Site"]:
                                self.assertEqual(score, "0.0")

    def test_correct_input_2_rows_persistent_columns_exist(self):
        rows = self.correct_input_2_rows_output
        self.assert_persistent_columns_exist(rows)

    def test_correct_input_2_rows_persistent_columns_correct(self):
        rows = self.correct_input_2_rows_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_persistent_columns_correct_2_rows(r1, r2)

    def test_correct_input_2_rows_10_description_match_columns(self):
        rows = self.correct_input_2_rows_output
        self.assert_10_match_columns(rows)

    def test_correct_input_2_rows_new_columns_exist(self):
        rows = self.correct_input_2_rows_output
        self.assert_new_columns_exist(rows)

    def test_correct_input_2_rows_match_site_correct(self):
        rows = self.correct_input_2_rows_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_match_site_2_rows_correct(r1, r2)

    def test_correct_input_2_rows_oem_match_correct(self):
        rows = self.correct_input_2_rows_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_oem_match_2_rows_correct(r1, r2)

    def test_correct_input_2_rows_description_match_correct(self):
        rows = self.correct_input_2_rows_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_correct_input_2_rows_extra_match_rows_empty(self):
        rows = self.correct_input_2_rows_output
        self.assert_extra_match_columns_empty(rows, start_index = 1)

    def test_correct_input_2_rows_old_row_correct(self):
        rows = self.correct_input_2_rows_output
        self.assert_old_rows_no(rows)

    def test_correct_input_2_rows_whitespace_persistent_columns_exist(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_persistent_columns_exist(rows)

    def test_correct_input_2_rows_whitespace_persistent_columns_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_persistent_columns_correct_2_rows(r1, r2)

    def test_correct_input_2_rows_whitespace_10_description_match_columns(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_10_match_columns(rows)

    def test_correct_input_2_rows_whitespace_new_columns_exist(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_new_columns_exist(rows)

    def test_correct_input_2_rows_whitespace_match_site_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_match_site_2_rows_correct(r1, r2)

    def test_correct_input_2_rows_whitespace_oem_match_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_oem_match_2_rows_correct(r1, r2)

    def test_correct_input_2_rows_whitespace_description_match_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        r1 = rows[0]
        r2 = rows[1]
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_correct_input_2_rows_whitespace_extra_match_rows_empty(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_extra_match_columns_empty(rows, start_index = 1)

    def test_correct_input_2_rows_whitespace_old_row_correct(self):
        rows = self.correct_input_2_rows_whitespace_output
        self.assert_old_rows_no(rows)

    def test_correct_input_2_rows_only_1_site_empty(self):
        rows = self.correct_input_2_rows_only_1_site_output
        self.assertEqual([], rows)

    def test_correct_input_3_rows_correct_columns(self):
        rows = self.correct_input_3_rows_output
        self.assert_output_fieldnames_correct(rows)

    #def test_correct_input_3_rows_match_site_not_site(self):
    #    rows = self.correct_input_3_rows_output
    #    self.assert_match_site_not_site(rows)

    def test_correct_input_3_rows_no_oem_code_matches(self):
        rows = self.correct_input_3_rows_output
        self.assert_no_oem_code_matches(rows)

    def test_correct_input_3_rows_description_matches_correct(self):
        rows = self.correct_input_3_rows_output
        self.assert_description_match_3_rows_correct(rows[0], rows[1], rows[2])

    def test_correct_2_inputs_and_outputs_things_that_should_always_be_true(self):
        rows = self.correct_2_inputs_and_outputs_output
        self.assert_things_that_should_always_be_true(rows)

    def test_correct_2_inputs_and_outputs_description_matches_correct(self):
        rows = self.correct_2_inputs_and_outputs_output
        r1, r2, r3, r4 = rows
        self.assertEqual(len(rows), 4)
        self.assert_description_match_2_correct_inputs_and_outputs_correct(r1,r2,r3,r4)
        
    def test_correct_2_inputs_3_outputs_1_unchanged_things_that_should_always_be_true(self):
        rows = self.correct_2_inputs_3_outputs_1_unchanged_output
        self.assert_things_that_should_always_be_true(rows)

    def test_correct_2_inputs_3_outputs_1_unchanged_description_matches_correct(self):
        rows = self.correct_2_inputs_3_outputs_1_unchanged_output
        r2, r3, r4 = rows
        self.assertEqual(len(rows), 3)
        self.assert_description_match_2_inputs_3_outputs_1_unchanged_correct(r2,r3,r4)

    def test_correct_2_inputs_oem_match_things_that_should_always_be_true(self):
        rows = self.correct_2_inputs_oem_match_output
        self.assert_things_that_should_always_be_true(rows)
    
    def test_correct_2_inputs_oem_match_description_match_correct(self):
        rows = self.correct_2_inputs_oem_match_output
        self.assert_extra_match_columns_empty(rows, start_index=0)
    
    def test_correct_2_inputs_oem_match_oem_match_correct(self):
        rows = self.correct_2_inputs_oem_match_output
        r1,r2 = rows
        self.assert_oem_match_2_inputs_oem_match_correct(r1, r2)

    def test_1_empty_description_3_rows_things_that_should_always_be_true(self):
        rows = self.one_empty_description_3_rows_output
        self.assert_things_that_should_always_be_true(rows)

    def test_1_empty_description_3_rows_empty_description_gives_poor_matches(self):
        rows = self.one_empty_description_3_rows_output
        self.assert_empty_descriptions_should_give_poor_matches(rows)

    def test_1_empty_description_3_rows_other_descriptions_match_normally(self):
        rows = self.one_empty_description_3_rows_output
        r1, r2, _ = rows
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_1_None_description_3_rows_things_that_should_always_be_true(self):
        rows = self.one_None_description_3_rows_output
        self.assert_things_that_should_always_be_true(rows)

    def test_1_None_description_3_rows_None_description_gives_poor_matches(self):
        rows = self.one_None_description_3_rows_output
        self.assert_empty_descriptions_should_give_poor_matches(rows)

    def test_1_None_description_3_rows_other_descriptions_match_normally(self):
        rows = self.one_None_description_3_rows_output
        r1, r2, _ = rows
        self.assert_description_match_2_rows_correct(r1, r2)

    def test_missing_description_2_rows_things_that_should_always_be_true(self):
        rows = self.missing_description_2_rows_output
        self.assert_things_that_should_always_be_true(rows)

    #TODO: Multiple sites, more missing columns, etc


if __name__ == "__main__":
    unittest.main()
    #import file_utils
    #file_utils.save_csv("test_out.csv", match_1_None_Description_3_rows(), fieldnames=site_matcher.output_fieldnames())
