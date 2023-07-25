import sys
from pathlib import Path
from typing import List, Optional

from robot.api import ExecutionResult, TestSuiteBuilder

from sherlock.config import BUILT_IN, Config
from sherlock.model import Library, Resource, Tree
from sherlock.report import get_reports
from sherlock.visitor import StructureVisitor


class Sherlock:
    def __init__(self, config: Optional[Config] = None):
        self.config = Config() if config is None else config
        self.reports = get_reports(self.config.report)
        self.resources = dict()
        self.directory = None
        self.packages: List[Tree] = []
        self.from_output = bool(self.config.output)

    def run(self):
        self.log("Sherlock analysis of Robot Framework code:\n")
        root = self.config.path
        self.log(f"Using {root.resolve()} as source repository")
        if self.config.pythonpath:
            sys.path = self.config.pythonpath + sys.path

        if self.from_output:
            suite = ExecutionResult(self.config.output).suite
            self.log(f"Loaded {self.config.output.resolve()} output file")
        else:
            suite = TestSuiteBuilder().build(self.config.path)

        tree = self.map_resources_for_path(root)
        self.packages.append(tree)
        self.packages.append(self.create_builtin_tree())
        self.packages.extend(self.map_resources())

        code_visitor = StructureVisitor(self.resources, self.from_output, self.config.robot_settings)
        suite.visit(code_visitor)
        for error in code_visitor.errors:
            self.log(error)

        self.report()

    def log(self, line: str):
        print(line, file=self.config.log_output)

    def report(self):
        for tree in self.packages:
            if not self.config.include_builtin and tree.name == BUILT_IN:
                continue
            for report in self.reports.values():
                report.get_report(tree, tree.name, self.config.root)

    def map_resources_for_path(self, root: Path):
        tree = Tree.from_directory(path=root, gitignore=self.config.default_gitignore)
        self.resources.update({path: resource for path, resource in tree.get_resources()})
        return tree

    def map_resources(self):
        for resource in self.config.resource:
            resource = Path(resource)
            resolved = resource.resolve()  # TODO search in pythonpaths etc, iterate over directories if not file
            if resolved.is_dir():
                yield self.map_resources_for_path(resolved)
            else:
                if not resolved.exists() or resolved.suffix == ".py":
                    res_model = Library(resolved)
                else:
                    res_model = Resource(resolved)
                self.resources[str(resolved)] = res_model
                tree = Tree(name=resource.name)
                tree.children.append(res_model)
                yield tree

    def create_builtin_tree(self):
        built_in = Library(BUILT_IN)
        built_in.load_library([], [], "builtin")
        built_in.filter_not_used = True
        built_in.builtin = True

        self.resources[BUILT_IN] = built_in
        tree = Tree(name=BUILT_IN)
        tree.children.append(built_in)
        return tree
