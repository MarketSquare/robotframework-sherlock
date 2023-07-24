from pathlib import Path

from tests.atest import AcceptanceTest, Keyword, Tree


class TestSearchOrder1(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "search_order_1")
    TEST_PATH = ""

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="search_order_1",
            children=[
                Tree(
                    name="a.resource",
                    res_type="Resource",
                    keywords=[Keyword(name="Duplicated", used=0), Keyword(name="Keyword", used=1)],
                ),
                Tree(name="suite.robot", keywords=[Keyword(name="Duplicated", used=1)]),
            ],
        )
        self.should_match_tree(expected, data)


class TestSearchOrder2(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "search_order_2")
    TEST_PATH = ""

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="search_order_2",
            children=[
                Tree(name="a.resource", res_type="Resource", keywords=[Keyword(name="Duplicated", used=0)]),
                Tree(
                    name="b.resource",
                    res_type="Resource",
                    keywords=[Keyword(name="Duplicated", used=0), Keyword(name="Keyword", used=1)],
                ),
                Tree(name="suite.robot", keywords=[Keyword(name="Duplicated", used=1)]),
            ],
        )
        self.should_match_tree(expected, data)


class TestSearchOrder3(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "search_order_3")
    TEST_PATH = ""

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="search_order_3",
            children=[
                Tree(name="a.resource", res_type="Resource", keywords=[Keyword(name="Duplicated in resource", used=1)]),
                Tree(
                    name="b.resource",
                    res_type="Resource",
                    keywords=[Keyword(name="Duplicated in resource", used=0), Keyword(name="Keyword", used=1)],
                ),
                Tree(name="suite.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)


class TestSearchOrder4(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "search_order_4")
    TEST_PATH = ""

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="search_order_4",
            children=[
                Tree(name="a.resource", res_type="Resource", keywords=[Keyword(name="1", used=0)]),
                Tree(name="b.resource", res_type="Resource", keywords=[Keyword(name="Keyword", used=1)]),
                Tree(name="from_b.resource", res_type="Resource", keywords=[Keyword(name="1", used=1)]),
                Tree(name="suite.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)


class TestSearchOrder5(AcceptanceTest):
    ROOT = Path(Path(__file__).parent, "search_order_5")
    TEST_PATH = ""

    def test(self):
        data = self.run_sherlock()
        expected = Tree(
            name="search_order_5",
            children=[
                Tree(name="a.resource", res_type="Resource", keywords=[Keyword(name="Keyword", used=1)]),
                Tree(
                    name="b.resource",
                    res_type="Resource",
                    keywords=[Keyword(name="Something that a.resource needs", used=1)],
                ),
                Tree(name="suite.robot", keywords=[]),
            ],
        )
        self.should_match_tree(expected, data)
