import os
from pathlib import Path

from robot.api import TestSuiteBuilder, ExecutionResult
from robot.model.keyword import Keyword
from robot.variables import Variables

from sherlock.config import Config
from sherlock.model import Library, Resource, Directory


def normalize_name(name):
    if not name:
        return ""
    return name.lower().replace(" ", "").replace("_", "")  # TODO: check how RF normalizes, is that all?


class Sherlock:
    def __init__(self):
        self.config = Config()
        self.resources = dict()
        self.directory = None
        self.variables = Variables()
        self.variables["${/}"] = os.path.sep

    def run(self):
        self.log("Sherlock analysis of Robot Framework code:\n")
        root = self.config.path
        self.log(f"Using {root.resolve()} as source repository")

        if self.config.output_path:
            suite = ExecutionResult(self.config.output_path).suite
            self.log(f"Loaded {self.config.output_path.resolve()} output file")
        else:
            suite = TestSuiteBuilder().build(self.config.path)

        self.map_resources(root)

        self.visit_suite(suite)

        self.log(self.directory.log_tree())

    def log(self, line):
        print(line, file=self.config.log_output)

    def map_resources(self, root):
        # TODO if provided a file it should still work (ie take parent of it)
        self.directory = Directory.root(root)
        self.resources = {path: resource for path, resource in self.directory.get_resources()}

    def get_local_variables(self, suite):
        variables = Variables()
        variables.update(self.variables)

        for variable in suite.resource.variables:
            variables[variable.name] = variable.value[0]  # TODO scalars
        variables["${CURDIR}"] = Path(suite.resource.source).parent

        return variables

    def visit_suite(self, suite):
        search_in = set()
        errors = set()
        # set them from --variables and such
        if hasattr(suite, "resource"):
            search_in.add(suite.resource.source)
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
                # search_in.add(name)
        else:
            # handle libname (such as resourceA) with accordance to possible paths
            if suite.source in self.resources:
                search_in.add(suite.source)

        for test in suite.tests:
            self.visit_keyword(test, search_in, errors)
        if errors:
            self.log(f"\nErrors in {suite.source}:")
        for error in errors:
            self.log(error)
        for sub_suite in suite.suites:
            self.visit_suite(sub_suite)

    def visit_keyword(self, kw, search_in, errors):
        if isinstance(kw, Keyword):
            name = kw.kwname if hasattr(kw, "kwname") else kw.name
            # TODO can match by resource name if executed with output.xml (resourceA.Keyword 3)
            found = []
            for resource in search_in:
                # if resource in resources:
                found += self.resources[resource].search(name, self.resources)
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
