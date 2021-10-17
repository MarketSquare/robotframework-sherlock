import argparse
import os
from pathlib import Path
from robot.api import TestSuiteBuilder, get_resource_model, ExecutionResult
from robot.running.builder import ResourceFileBuilder
from robot.libraries import STDLIBS
from robot.utils import Importer
from robot.running.userkeyword import UserLibrary
from robot.running.testlibraries import TestLibrary
from robot.running.arguments import EmbeddedArguments
import ast
from robot.libdocpkg.robotbuilder import KeywordDocBuilder, LibraryDocBuilder, ResourceDocBuilder
from jinja2 import Template
from itertools import chain

from .file_utils import get_paths, ResultTree


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
        self.loaded = False  # lazy loading
        self.keywords = dict()
        # TODO embedded keywords?

    def load_library(self, args):
        if self.loaded:
            return
        # TODO handle exceptions (not enough args etc)
        name = str(self.path)
        if args:
            name += '::' + ':'.join(args)
        lib_doc = LibraryDocBuilder().build(name)  # TODO load specs etc optionally
        self.keywords = {normalize_name(kw.name): KeywordStats(kw.name) for kw in lib_doc.keywords}
        self.loaded = True

    def search(self, name, resources):
        name = normalize_name(name)
        if name in self.keywords:
            self.keywords[name].used += 1
            # resources[self.path] = self

    def __str__(self):
        s = f"Library: {self.path}\n"
        if self.keywords:
            s += f"  Keywords:\n"
            for name, kw in self.keywords.items():
                s += "    " + str(kw)
        return s


class Resource:
    def __init__(self, path: Path):
        self.path = str(path)
        self.directory = str(path.parent)
        self.resources = dict()
        model = get_resource_model(str(path), data_only=True, curdir=str(path.cwd()))
        visitor = ResourceVisitor()
        visitor.visit(model)
        self.keywords, self.embedded_keywords = visitor.keywords, visitor.embedded_keywords
        # set them from --variables and such
        variables = {'${/}': os.path.sep}
        self.imports = set()
        for resource in visitor.resources:
            for var, value in variables.items():
                resource = resource.replace(var, value)
            self.imports.add(str(Path(self.directory, resource).resolve()))
        self.libraries = dict()
        for library, args in visitor.libraries.items():
            for var, value in variables.items():
                library = library.replace(var, value)
            self.libraries[str(Path(self.directory, library).resolve())] = args

    def search(self, name, resources):
        normalized = normalize_name(name)  # TODO normalize once
        if normalized in self.keywords:
            self.keywords[normalized].used += 1
            resources[self.path] = self
            return
        # TODO handle embedded, not existing, in resources
        # for resource in self.resource.. resource.search.. TODO handle multiple matched
        found = False
        for imported in self.imports:
            if imported in resources:
                if normalized in resources[imported].keywords:
                    found = True  # check multiple
                    resources[imported].search(name, resources)
        for lib, args in self.libraries.items():
            if lib in resources:
                resources[lib].load_library(args)
                if normalized in resources[lib].keywords:
                    found = True
                    resources[lib].search(name, resources)
        if not found:
            for embedded in self.embedded_keywords:
                if embedded.match(name):
                    self.embedded_keywords[embedded].used += 1

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


def run():
    print("Sherlock")
    resources = dict()
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default=None)
    parser.add_argument("--output_path", type=str, default=None)
    config = parser.parse_args()
    if config.path is not None:  # TODO either one of them should be present (mutually exclusive)
        suite = TestSuiteBuilder().build(config.path)
        root = config.path
    elif config.output_path:
        suite = ExecutionResult(config.output_path).suite
        root = str(Path(config.output_path).parent)  # TODO if given xml file, should point to source dir


    #ns = Namespace()
    paths = get_paths((root,))
    for path in paths:
        # resource = ResourceFileBuilder().build(path)
        # user_library = UserLibrary(resource)
        if path.suffix == ".py":
            resources[str(path)] = Library(path)
        else:
            resources[str(path)] = Resource(path)
    visit_suite(suite, resources)
    for path, resource in resources.items():
        print(resource)

    # tree = ResultTree(Path(root)) # can be used later for html output format with tree


def visit_suite(suite, resources):
    # find def of given suite (*** Keywords)
    search_in = set()
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
            if name not in resources:
                continue
            if imported.type == 'Library':
                resources[name].load_library(imported.args)
            search_in.add(name)
    else:
        # handle libname (such as resourceA) with accordance to possible paths
        if suite.source in resources:
            search_in.add(suite.source)

    for test in suite.tests:
        visit_keyword(test, search_in, resources)
    for sub_suite in suite.suites:
        visit_suite(sub_suite, resources)


def visit_keyword(kw, search_in, resources):
    if getattr(kw, "type", "") == "KEYWORD":
        name = kw.kwname if hasattr(kw, 'kwname') else kw.name
        for resource in search_in:
            if resource in resources:
                resources[resource].search(name, resources)
    for sub_kw in getattr(kw, "body", ()):
        visit_keyword(sub_kw, search_in, resources)

# resources = { 'path/to/file.robot': Resource() }
# Resource().resource = 'path'. 'path'..
# included_extensions for TestSuiteBilder()

# resource = ResourceFileBuilder().build(path)
# self._resource_cache[path] = resource


#  KeywordStat(name=..(orig one), used,
# keywords = {normalize_name(name): KeywordStats(name=name)}
# go to test file, map imports to our Resource() or at least to ResourceFileBuilder for keyword searching
# whenever there is hit (keyword used from given resource), collect stats
