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


class TestLibraryFromResource:
    def test(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        run_sherlock(robot_output=robot_output, source=path_to_test_data, report=["json"])
        data = get_output("sherlock_test_data.json")
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="imports.resource", keywords=[]),
                Tree(
                    name="MyStuff",
                    keywords=[
                        Keyword(name="My Keyword", used=1),
                        Keyword(name="Not Used", used=0),
                        Keyword(name="Third Keyword", used=2),
                    ],
                ),
                Tree(name="test.robot", keywords=[]),
            ],
        ).to_json()
        assert match_tree(expected, data)