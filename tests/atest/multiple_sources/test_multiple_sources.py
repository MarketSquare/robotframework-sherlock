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


class TestMultipleSources:
    # def test_two_sources(self, path_to_test_data):
    #     robot_output = path_to_test_data / "output.xml"
    #     source1 = path_to_test_data / "resource1"
    #     source2 = path_to_test_data / "resource2"  # TODO
    #     run_sherlock(robot_output=robot_output, source=[source1, source2], report=["json"])

    def test_single_source(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        source = path_to_test_data / "resource1"
        run_sherlock(robot_output=robot_output, source=source, report=["json"])
        with open("sherlock_resource1.json") as f:
            data = json.load(f)
        # TODO used 0 since it doesn't know it was used by test.robot
        expected = Tree(
            name="resource1",
            children=[Tree(name="file.resource", keywords=[Keyword(name="Keyword 1", used=0, complexity=1)])],
        ).to_json()
        assert match_tree(expected, data)
