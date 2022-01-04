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


class TestDuplicatedNamesDotted:
    def test(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        run_sherlock(robot_output=robot_output, source=path_to_test_data, report=["json"])
        data = get_output("sherlock_test_data.json")
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="Library1", keywords=[Keyword(name="Keyword 1", used=2)]),
                Tree(name="Library2", keywords=[Keyword(name="Keyword 1", used=1)]),
                Tree(name="test.robot", keywords=[]),
            ],
        ).to_json()
        assert match_tree(expected, data)
