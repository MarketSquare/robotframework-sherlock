from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestInvalidLibrary(AcceptanceTest):
    ROOT = Path(__file__).parent / "test_data"

    def test(self):
        data = self.run_sherlock(report=["json", "print"])
        expected = Tree(
            name="test_data",
            children=[
                Tree(name="Library.py", keywords=[]),
                Tree(name="LibraryWithArgs.py", keywords=[]),
                Tree(name="LibraryWithFailingInit.py", keywords=[]),
                Tree(name="LibraryAccessRunning.py", keywords=[]),
                Tree(name="test.robot", keywords=[Keyword(name="Keyword 1", used=1, complexity=1)]),
            ],
        )
        self.should_match_tree(expected, data)
