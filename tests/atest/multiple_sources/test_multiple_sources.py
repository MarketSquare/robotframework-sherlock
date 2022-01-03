import json
from pathlib import Path

import pytest

from .. import run_sherlock, match_tree


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
        expected = {
            "name": "resource1",
            # "type": "Directory",
            "children": [
                {
                    "name": "file.resource",
                    # "type": "Resource",
                    "keywords": [
                        {
                            "name": "Keyword 1",
                            "used": 0,  # TODO 0 since it doesn't know it was used by test.robot
                            "complexity": 1,
                            # "status": "pass"
                        }
                    ],
                }
            ],
        }
        assert match_tree(expected, data)
