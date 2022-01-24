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


class TestImportWithVariable:
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
                        Tree(name="a.resource", keywords=[]),
                        Tree(
                            name="b.resource",
                            keywords=[Keyword(name="Internal Keyword", used=1), Keyword(name="Keyword 1", used=1)],
                        ),
                        Tree(
                            name="c.resource",
                            keywords=[Keyword(name="Internal Keyword", used=1), Keyword(name="Keyword 1", used=1)],
                        ),
                        Tree(name="test_a.robot", keywords=[Keyword(name="Internal Keyword", used=0)]),
                        Tree(name="test_b.robot", keywords=[]),
                    ],
                )
            ],
        ).to_json()
        assert match_tree(expected, data)
