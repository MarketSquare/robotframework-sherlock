from pathlib import Path

import pytest

from tests.atest import AcceptanceTest, Keyword, Tree


@pytest.mark.skip(reason="Library import with sleeps for timing tests")
class TestLibraryFromResource(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        data = self.run_sherlock()
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
        )
        self.should_match_tree(expected, data)
