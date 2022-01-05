import os
from pathlib import Path
from typing import Optional, List

from robot.api import TestSuiteBuilder, ExecutionResult
from robot.model.keyword import Keyword
from robot.variables import Variables

from sherlock.config import Config, BUILT_IN
from sherlock.model import Tree, Library, Resource
from sherlock.report import html_report, print_report, json_report


class Sherlock:
    def __init__(self, config: Optional[Config] = None):
        self.config = Config() if config is None else config
        self.resources = dict()
        self.directory = None
        self.packages: List[Tree] = []
        self.from_output = bool(self.config.output_path)
        self.variables = Variables()
        self.variables["${/}"] = os.path.sep

    def run(self):
        self.log("Sherlock analysis of Robot Framework code:\n")
        root = self.config.path
        self.log(f"Using {root.resolve()} as source repository")

        if self.from_output:
            suite = ExecutionResult(self.config.output_path).suite
            self.log(f"Loaded {self.config.output_path.resolve()} output file")
        else:
            suite = TestSuiteBuilder().build(self.config.path)

        tree = self.map_resources_for_path(root)
        self.packages.append(tree)
        self.packages.append(self.create_builtin_tree())
        self.packages.extend(self.map_resources())

        self.visit_suite(suite)

        self.report()

    def log(self, line: str):
        print(line, file=self.config.log_output)

    def report(self):
        for tree in self.packages:
            if not self.config.include_builtin and tree.name == BUILT_IN:
                continue
            if "print" in self.config.report:
                print_report(tree, tree.name, self.config.log_output)
            if "html" in self.config.report:
                html_report(tree, tree.name, self.config.root)
            if "json" in self.config.report:
                json_report(tree, tree.name, self.config.root)

    def map_resources_for_path(self, root: Path):
        tree = Tree.from_directory(path=root, gitignore=self.config.default_gitignore)
        self.resources.update({path: resource for path, resource in tree.get_resources()})
        return tree

    def map_resources(self):
        for resource in self.config.resource:
            resource = Path(resource)
            resolved = resource.resolve()  # TODO search in pythonpaths etc, iterate over directories if not file
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
        built_in.load_library()
        built_in.filter_not_used = True
        built_in.builtin = True

        self.resources[BUILT_IN] = built_in
        tree = Tree(name=BUILT_IN)
        tree.children.append(built_in)
        return tree

    def get_local_variables(self, suite):
        variables = Variables()
        variables.update(self.variables)

        for variable in suite.resource.variables:
            variables[variable.name] = variable.value[0]  # TODO scalars
        variables["${CURDIR}"] = Path(suite.resource.source).parent

        return variables

    def visit_suite(self, suite):
        search_in = None
        errors = set()
        # TODO set them from --variables and such
        if hasattr(suite, "resource"):
            search_in = suite.resource.source
            for imported in suite.resource.imports:
                if imported.type == "Variables":
                    continue
                name = imported.name
                variables = self.get_local_variables(suite)
                name = variables.replace_string(name, ignore_errors=True)  # TODO dont ignore errors
                # TODO: replace with better search taken from RF, check python path and such
                name = str(Path(imported.directory, name).resolve())
                if name not in self.resources:
                    continue
                if imported.type == "Library":
                    self.resources[name].load_library(imported.args)
        else:
            # handle libname (such as resourceA) with accordance to possible paths
            if suite.source in self.resources:
                search_in = suite.source

        if search_in is not None:
            for test in suite.tests:
                self.visit_keyword(test, search_in, errors)  # TODO visit test?
        if errors:
            self.log(f"\nErrors in {suite.source}:")
        for error in errors:
            self.log(error)
        for sub_suite in suite.suites:
            self.visit_suite(sub_suite)

    def visit_keyword(self, kw, search_in, errors):
        if isinstance(kw, Keyword):
            name = kw.kwname if self.from_output else kw.name
            libname = kw.libname if self.from_output else None
            found = self.resources[search_in].search(name, self.resources, libname)
            if not found:
                errors.add(f"Keyword '{name}' definition not found")
            elif len(found) > 1:
                s = f"Keyword '{name}' matches following resources/libraries:\n"
                # s += "\n".join(found)
                # s += "\n"
                errors.add(s)
            else:
                found[0].used += 1
        for sub_kw in getattr(kw, "body", ()):
            self.visit_keyword(sub_kw, search_in, errors)
