import json
from pathlib import Path

import pytest

from .. import run_sherlock, get_output, match_tree, Tree, Keyword


@pytest.fixture(scope="class")
def path_to_test_data():
    return Path(Path(__file__).parent, "test_data")


@pytest.fixture(scope="class")
def run_with_tests():
    return "test.robot"


class TestExternalLibrary:
    def test_external_not_in_resource_option(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        run_sherlock(robot_output=robot_output, source=path_to_test_data, report=["json"])
        data = get_output("sherlock_test_data.json")
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="test.robot", keywords=[]),
            ],
        ).to_json()
        assert match_tree(expected, data)

    def test_external_in_resource_option(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        run_sherlock(robot_output=robot_output, source=path_to_test_data, report=["json"], resource=["TemplatedData"])

        data = get_output("sherlock_test_data.json")
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="test.robot", keywords=[]),
            ],
        ).to_json()
        assert match_tree(expected, data)

        data = get_output("sherlock_TemplatedData.json")
        expected = Tree(
            name="TemplatedData",
            children=[
                Tree(
                    name="TemplatedData",
                    keywords=[
                        Keyword(name="Get Templated Data", used=0),
                        Keyword(name="Get Templated Data From Path", used=2),
                        Keyword(name="Normalize"),
                        Keyword(name="Return Data With Type"),
                    ],
                ),
            ],
        ).to_json()
        assert match_tree(expected, data)
