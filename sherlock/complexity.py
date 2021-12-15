from collections import defaultdict

from robot.api.parsing import ModelVisitor


class PathNode:
    def __init__(self, name):
        self.name = name


class ComplexityChecker(ModelVisitor):
    def __init__(self):
        self.nodes = defaultdict(list)
        self.graph = None
        self.tail = None

    def connect(self, node1, node2):
        self.nodes[node1].append(node2)
        self.nodes[node2] = []

    def complexity(self):
        """mccabe V-E+2"""
        edges = sum(len(n) for n in self.nodes.values())
        nodes = len(self.nodes)
        return edges - nodes + 2

    def append_path_node(self, name):
        if not self.tail:
            return
        path_node = PathNode(name)
        self.connect(self.tail, path_node)
        self.tail = path_node
        return path_node

    def visit_Keyword(self, node):  # noqa
        name = f"{node.name}:{node.lineno}:{node.col_offset}"
        path_node = PathNode(name)
        self.tail = path_node
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        name = f"KeywordCall {node.lineno}"
        self.append_path_node(name)

    def visit_For(self, node):  # noqa
        name = f"FOR {node.lineno}"
        path_node = self.append_path_node(name)
        self._parse_subgraph(node, path_node)

    def visit_If(self, node):  # noqa
        name = f"IF {node.lineno}"
        path_node = self.append_path_node(name)
        self._parse_subgraph(node, path_node)

    def _parse_subgraph(self, node, path_node):
        loose_ends = []
        self.tail = path_node
        self.generic_visit(node)
        loose_ends.append(self.tail)
        if getattr(node, "orelse", False):
            self.tail = path_node
            self.generic_visit(node.orelse)
            loose_ends.append(self.tail)
        else:
            loose_ends.append(path_node)
        if path_node:
            bottom = PathNode("")
            for loose_end in loose_ends:
                self.connect(loose_end, bottom)
            self.tail = bottom
