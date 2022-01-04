import json
from pathlib import Path

import pytest

from .. import run_sherlock, match_tree, Tree, Keyword


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
        with open("sherlock_test_data.json") as f:
            data = json.load(f)
        expected = Tree(
            name="test_data",
            children=[Tree(name="Library", keywords=[Keyword(name="Keyword 1", used=2)]),
                      Tree(name="test.robot", keywords=[]),
                      Tree(name="__pycache__")],  # FIXME
        ).to_json()
        assert match_tree(expected, data)
