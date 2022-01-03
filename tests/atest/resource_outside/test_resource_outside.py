import json
from pathlib import Path

import pytest

from .. import run_sherlock, match_tree


@pytest.fixture(scope="class")
def path_to_test_data():
    return Path(__file__).parent / "test_data" / "tests"


@pytest.fixture(scope="class")
def run_with_tests():
    return "test.robot"


class TestResourceOutside:
    def test_resource_outside(self, path_to_test_data):
        robot_output = path_to_test_data / "output.xml"
        # FIXME when path is directory, PermissionError is raised
        resource = path_to_test_data.parent / "resource1" / "file.resource"
        run_sherlock(robot_output=robot_output, source=path_to_test_data, report=["json"], resource=[resource])
        with open("sherlock_tests.json") as f:
            data = json.load(f)
        expected = {
            "name": "tests",
            # "type": "Directory",
            "children": [
                {
                    "name": "resource2",
                    # "type": "Directory",
                    "children": [
                        {
                            "name": "file2.resource",
                            "keywords": [
                                {
                                    "name": "Keyword 2",
                                    "used": 1,
                                    "complexity": 1,
                                    # "status": "pass"
                                },
                                {
                                    "name": "Keyword 3",
                                    "used": 0,
                                    "complexity": 1,
                                    # "status": "pass"
                                },
                            ],
                        },
                    ],
                },
                {"name": "test.robot", "keywords": []},
            ],
        }
        assert match_tree(expected, data)
        with open("sherlock_file.resource.json") as f:
            data = json.load(f)
        expected = {
            "name": "file.resource",
            "children": [{
                "name": "file.resource",  # TODO fix trees for single files
                "keywords": [
                    {
                        "name": "Keyword 1",
                        "used": 1,
                        "complexity": 1,
                        # "status": "pass"
                    },
                ]
            }
            ]
        }
        assert match_tree(expected, data)
