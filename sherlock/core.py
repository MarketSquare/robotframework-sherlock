import os
from pathlib import Path

from robot.api import TestSuiteBuilder, ExecutionResult
from robot.model.keyword import Keyword

from sherlock.config import Config
from sherlock.file_utils import get_paths
from sherlock.model import Library, Resource


def normalize_name(name):
    if not name:
        return ''
    return name.lower().replace(' ', '').replace('_', '')  # TODO: check how RF normalizes, is that all?


class Sherlock:
    def __init__(self):
        self.config = Config()
        self.resources = dict()

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

        for path, resource in self.resources.items():
            self.log(resource)

    def log(self, line):
        print(line, file=self.config.log_output)
    
    def map_resources(self, root):
        built_in = Library("BuiltIn")
        built_in.load_library()
        built_in.filter_not_used = True
        self.resources["BuiltIn"] = built_in

        paths = get_paths((root,))
        for path in paths:
            if path.suffix == ".py":
                self.resources[str(path)] = Library(path)
            else:
                self.resources[str(path)] = Resource(path)

    def visit_suite(self, suite):
        search_in = set()
        errors = set()
        # set them from --variables and such
        variables = {'${/}': os.path.sep}
        if hasattr(suite, 'resource'):
            search_in.add(suite.resource.source)
            for imported in suite.resource.imports:
                if imported.type == 'Variables':
                    continue
                name = imported.name
                for var, value in variables.items():
                    name = name.replace(var, value)
                # TODO: replace with better search taken from RF, check python path and such
                name = str(Path(imported.directory, name).resolve())
                if name not in self.resources:
                    continue
                if imported.type == 'Library':
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
            name = kw.kwname if hasattr(kw, 'kwname') else kw.name
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
