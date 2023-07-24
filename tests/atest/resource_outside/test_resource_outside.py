from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree, get_output


class TestResourceOutside(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data" / "tests"

    def test_resource_outside(self):
        # FIXME when path is directory, PermissionError is raised
        resource = self.ROOT.parent / "resource1" / "file.resource"
        data = self.run_sherlock(resource=[resource])
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
        )
        self.should_match_tree(expected, data)
        data = get_output("sherlock_file.resource.json")
        # TODO fix trees for single files
        expected = Tree(
            name="file.resource",
            children=[Tree(name="file.resource", keywords=[Keyword(name="Keyword 1", used=1, complexity=1)])],
        )
        self.should_match_tree(expected, data)
