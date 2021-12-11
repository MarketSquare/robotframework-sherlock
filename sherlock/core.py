import ast
import os
from itertools import chain
from pathlib import Path

from robot.api import TestSuiteBuilder, get_resource_model, ExecutionResult
from robot.model.keyword import Keyword
from robot.running.arguments import EmbeddedArguments
from robot.running.testlibraries import TestLibrary
from robot.running.userkeyword import UserLibrary
from robot.running.importer import Importer

from sherlock.config import Config
from sherlock.file_utils import get_paths


def normalize_name(name):
    if not name:
        return ''
    return name.lower().replace(' ', '').replace('_', '')  # TODO: check how RF normalizes, is that all?


class KeywordStats:
    def __init__(self, name):
        self.name = name
        self.used = 0
        self.body = []  # TODO: visit and fill

    def __str__(self):
        return f"{self.name} | Used: {self.used}\n"


class Library:
    def __init__(self, path):
        self.path = path
        self.keywords = dict()
        self.library = None
        self.filter_not_used = False

    def load_library(self, args=None):
        if self.library:
            return
        # TODO handle exceptions (not enough args etc)
        name = str(self.path)
        self.library = TestLibrary(name, args)
        for keyword in self.library.handlers:
            self.keywords[keyword.name] = KeywordStats(keyword.name)

    def search(self, name, found, *args):
        if name in self.library.handlers:
            handler = self.library.handlers[name]
            found.append(f"Keyword '{handler.name}' in {self.path}")
            self.keywords[handler.name].used += 1
            return True
        return False

    def __str__(self):
        s = f"Library: {self.path}\n"
        if self.keywords:
            s += f"  Keywords:\n"
            for name, kw in self.keywords.items():
                if self.filter_not_used and not kw.used:
                    continue
                s += "    " + str(kw)
        return s


class Resource:
    def __init__(self, path: Path):
        self.path = str(path)
        self.directory = str(path.parent)
        self.resources = dict()
        self.imports = set()
        self.libraries = dict()

        model = get_resource_model(str(path), data_only=True, curdir=str(path.cwd()))
        visitor = ResourceVisitor()
        visitor.visit(model)
        self.keywords, self.embedded_keywords = visitor.keywords, visitor.embedded_keywords
        # set them from --variables and such
        variables = {'${/}': os.path.sep}
        for resource in visitor.resources:
            for var, value in variables.items():
                resource = resource.replace(var, value)
            self.imports.add(str(Path(self.directory, resource).resolve()))
        for library, args in visitor.libraries.items():
            for var, value in variables.items():
                library = library.replace(var, value)
            self.libraries[str(Path(self.directory, library).resolve())] = args

    def search(self, name, normalized, resources, prev_found):
        if resources["BuiltIn"].search(name, prev_found, resources):
            return
        if normalized in self.keywords:
            prev_found.append(f"Keyword '{self.keywords[normalized].name}' in {self.path}")
            self.keywords[normalized].used += 1
            resources[self.path] = self
        for imported in self.imports:
            if imported in resources:
                resources[imported].search(name, normalized, resources, prev_found)
        for lib, args in self.libraries.items():
            if lib in resources:
                resources[lib].load_library(args)
                resources[lib].search(name, prev_found, resources)
        for pattern, keyword in self.embedded_keywords.items():
            if pattern.match(name):
                prev_found.append(f"Keyword '{keyword.name}' in {self.path}")
                self.embedded_keywords[pattern].used += 1

    def __str__(self):
        s = f"File: {self.path}\n"
        if self.keywords or self.embedded_keywords:
            s += f"  Keywords:\n"
            for kw in chain(self.keywords.values(), self.embedded_keywords.values()):
                s += "    " + str(kw)
        return s


class ResourceVisitor(ast.NodeVisitor):
    def __init__(self):
        self.keywords = dict()
        self.embedded_keywords = dict()
        self.resources = set()
        self.libraries = dict()

    # def visit_File(self): TODO: make singleton

    def visit_Keyword(self, node):  # noqa
        embedded = EmbeddedArguments(node.name)
        if embedded:
            self.embedded_keywords[embedded.name] = KeywordStats(node.name)
        else:
            self.keywords[normalize_name(node.name)] = KeywordStats(node.name)  # TODO: handle duplications

    def visit_ResourceImport(self, node):  # noqa
        if node.name:
            self.resources.add(node.name)

    def visit_LibraryImport(self, node):  # noqa
        # TODO aliases
        if node.name:
            self.libraries[node.name] = node.args


class Sherlock:
    def __init__(self):
        self.config = Config()
        self.resources = dict()

    def run(self):
        self.log("Sherlock analysis of Robot Framework code:\n")
        resources = dict()
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
        # find def of given suite (*** Keywords)
        search_in = set()
        errors = set()
        # TODO if no tests, skip counting
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
                search_in.add(name)
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
                self.resources[resource].search(name, normalize_name(name), self.resources, found)
            if not found:
                errors.add(f"Keyword '{name}' definition not found")
            elif len(found) > 1:
                s = f"Keyword '{name}' matches following resources/libraries:\n"
                s += "\n".join(found)
                s += "\n"
                errors.add(s)
        for sub_kw in getattr(kw, "body", ()):
            self.visit_keyword(sub_kw, search_in, errors)
