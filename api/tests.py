from django.test import TestCase
import unittest
unittest.TestLoader.sortTestMethodsUsing = None


import api.spreadsheet_actions

# Create your tests here.


class SpreadheetActions(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.gc = api.spreadsheet_actions.gc
        spreadsheet = cls.gc.create("Test Spreasheet")
        cls.spreadsheet_id = spreadsheet.id

        worksheet1 = spreadsheet.add_worksheet(title="worksheet1", rows="2", cols="3")
        worksheet1.append_row(["id", "heading_a", "heading_b"])
        worksheet1.append_row(["1", "value_a", "value_b"])

        worksheet2 = spreadsheet.add_worksheet(title="worksheet2", rows="2", cols="3")
        worksheet2.append_row(["id", "heading_x", "heading_y"])
        worksheet2.append_row(["1", "value_x", "value_y"])

    @classmethod
    def tearDownClass(cls):
        cls.gc.del_spreadsheet(cls.spreadsheet_id)

    def test_001_get_sheets_values(self):
        self.assertEqual(
            api.spreadsheet_actions.sheets_data(
                self.spreadsheet_id, ["worksheet1", "worksheet2"]
            ),
            {
                "worksheet1": {
                    "headings": ["id", "heading_a", "heading_b"],
                    "records": [
                        {"id": "1", "heading_a": "value_a", "heading_b": "value_b"}
                    ],
                    "records_by_id": {
                        "1": {"id": "1", "heading_a": "value_a", "heading_b": "value_b"}
                    },
                    "data": [["1", "value_a", "value_b"]],
                    "count": 1,
                    "id_to_row_number": {"1": 0},
                },
                "worksheet2": {
                    "headings": ["id", "heading_x", "heading_y"],
                    "records": [
                        {"id": "1", "heading_x": "value_x", "heading_y": "value_y"}
                    ],
                    "records_by_id": {
                        "1": {"id": "1", "heading_x": "value_x", "heading_y": "value_y"}
                    },
                    "data": [["1", "value_x", "value_y"]],
                    "count": 1,
                    "id_to_row_number": {"1": 0},
                },
            },
        )

    def test_002_add_new_row(self):
        api.spreadsheet_actions.insert_row(
            self.spreadsheet_id,
            "worksheet1",
            {"id": "2", "heading_a": "value_a2", "heading_b": "value_b2"},
        )

        self.assertEqual(
            api.spreadsheet_actions.sheets_data(self.spreadsheet_id, ["worksheet1"]),
            {
                "worksheet1": {
                    "headings": ["id", "heading_a", "heading_b"],
                    "records": [
                        {"id": "1", "heading_a": "value_a", "heading_b": "value_b"},
                        {"id": "2", "heading_a": "value_a2", "heading_b": "value_b2"},
                    ],
                    "records_by_id": {
                        "1": {
                            "id": "1",
                            "heading_a": "value_a",
                            "heading_b": "value_b",
                        },
                        "2": {
                            "id": "2",
                            "heading_a": "value_a2",
                            "heading_b": "value_b2",
                        },
                    },
                    "data": [
                        ["1", "value_a", "value_b"],
                        ["2", "value_a2", "value_b2"],
                    ],
                    "count": 2,
                    "id_to_row_number": {"1": 0, "2": 1},
                },
            },
        )


    def test_003_update_existing_row(self):
        api.spreadsheet_actions.insert_row(
            self.spreadsheet_id,
            "worksheet1",
            {"id": "1", "heading_a": "value_a1", "heading_b": "value_b1"},
        )

        self.assertEqual(
            api.spreadsheet_actions.sheets_data(self.spreadsheet_id, ["worksheet1"]),
            {
                "worksheet1": {
                    "headings": ["id", "heading_a", "heading_b"],
                    "records": [
                        {"id": "1", "heading_a": "value_a1", "heading_b": "value_b1"},
                        {"id": "2", "heading_a": "value_a2", "heading_b": "value_b2"},
                    ],
                    "records_by_id": {
                        "1": {
                            "id": "1",
                            "heading_a": "value_a1",
                            "heading_b": "value_b1",
                        },
                        "2": {
                            "id": "2",
                            "heading_a": "value_a2",
                            "heading_b": "value_b2",
                        },
                    },
                    "data": [
                        ["1", "value_a1", "value_b1"],
                        ["2", "value_a2", "value_b2"],
                    ],
                    "count": 2,
                    "id_to_row_number": {"1": 0, "2": 1},
                },
            },
        )


    def test_004_delete_row(self):
        api.spreadsheet_actions.delete_row(
            self.spreadsheet_id,
            "worksheet1",
            "1"
        )

        self.assertEqual(
            api.spreadsheet_actions.sheets_data(self.spreadsheet_id, ["worksheet1"]),
            {
                "worksheet1": {
                    "headings": ["id", "heading_a", "heading_b"],
                    "records": [
                        {"id": "2", "heading_a": "value_a2", "heading_b": "value_b2"}
                    ],
                    "records_by_id": {
                        "2": {"id": "2", "heading_a": "value_a2", "heading_b": "value_b2"}

                    },
                    "data": [["2", "value_a2", "value_b2"]],
                    "count": 1,
                    "id_to_row_number": {"2": 0},
                },
            }
        )


class TestAPI(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.gc = api.spreadsheet_actions.gc
        spreadsheet = cls.gc.create("Test Spreasheet")
        cls.spreadsheet_id = spreadsheet.id

        worksheet1 = spreadsheet.add_worksheet(title="worksheet1", rows="2", cols="3")
        worksheet1.append_row(["id", "heading_a", "heading_b"])
        worksheet1.append_row(["1", "value_a", "value_b"])

        worksheet2 = spreadsheet.add_worksheet(title="Control", rows="2", cols="3")
        worksheet2.append_row(["id", "heading_x", "heading_y"])
        worksheet2.append_row(["1", "value_x", "value_y"])

    @classmethod
    def tearDownClass(cls):
        cls.gc.del_spreadsheet(cls.spreadsheet_id)

    def test_001_get_sheets_values(self):
