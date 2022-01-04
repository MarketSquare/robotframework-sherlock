import json
from pathlib import Path

import pytest

from .. import run_sherlock, match_tree, get_output, Tree, Keyword


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
        data = get_output("sherlock_tests.json")
        expected = Tree(
            name="tests",
            children=[
                Tree(
                    name="resource2",
                    children=[
                        Tree(
                            name="file2.resource",
                            keywords=[
                                Keyword(name="Keyword 2", used=1, complexity=1),
                                Keyword(name="Keyword 3", used=0, complexity=1),
                            ],
                        )
                    ],
                ),
                Tree(name="test.robot", keywords=[]),
            ],
        ).to_json()
        assert match_tree(expected, data)
        data = get_output("sherlock_file.resource.json")
        # TODO fix trees for single files
        expected = Tree(
            name="file.resource",
            children=[Tree(name="file.resource", keywords=[Keyword(name="Keyword 1", used=1, complexity=1)])],
        ).to_json()
        assert match_tree(expected, data)
