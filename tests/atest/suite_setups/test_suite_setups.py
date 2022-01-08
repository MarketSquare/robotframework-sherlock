import json
from pathlib import Path

import pytest

from .. import run_sherlock, get_output, match_tree, Tree, Keyword


@pytest.fixture(scope="class")
def path_to_test_data():
    return Path(Path(__file__).parent, "test_data")


@pytest.fixture(scope="class")
def run_with_tests():
    return "tests"


class TestSuiteSetups:
    def test(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        run_sherlock(robot_output=robot_output, source=path_to_test_data, report=["json", "html"])
        data = get_output("sherlock_test_data.json")
        expected = Tree(
            name="test_data",
            children=[
                Tree(
                    name="tests",
                    children=[
                        Tree(
                            name="resource.robot",
                            keywords=[Keyword(name="Other Keyword", used=6), Keyword(name="Suite Keyword", used=2)],
                        ),
                        Tree(name="tests.robot", keywords=[Keyword(name="Internal Keyword", used=1)]),
                        Tree(name="__init__.robot", keywords=[Keyword(name="Suite Keyword", used=2)]),
                    ],
                )
            ],
        ).to_json()
        assert match_tree(expected, data)
