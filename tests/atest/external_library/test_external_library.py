from pathlib import Path

from .. import get_output, Tree, Keyword, AcceptanceTest


class TestExternalLibrary(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test_external_not_in_resource_option(self):
        data = self.run_sherlock()
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="test.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)

    def test_external_in_resource_option(self):
        data = self.run_sherlock(resource=["TemplatedData"])

        expected = Tree(
            name="test_data",
            children=[
                Tree(name="test.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)

        data = get_output("sherlock_TemplatedData.json")
        expected = Tree(
            name="TemplatedData",
            children=[
                Tree(
                    name="TemplatedData",
                    keywords=[
                        Keyword(name="Get Templated Data", used=0),
                        Keyword(name="Get Templated Data From Path", used=2),
                        Keyword(name="Normalize"),
                        Keyword(name="Return Data With Type"),
                    ],
                ),
            ],
        )
        self.should_match_tree(expected, data)
