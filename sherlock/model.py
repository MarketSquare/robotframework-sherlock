import ast
import os
import textwrap
import math
from pathlib import Path
from typing import Optional

import robot.errors
from rich.table import Table
from pathspec import PathSpec

from robot.api import get_model
from robot.running.arguments import EmbeddedArguments
from robot.running.testlibraries import TestLibrary
from robot.variables import Variables
from robot.utils import NormalizedDict, find_file
from robot.errors import DataError
from tabulate import tabulate

from sherlock.complexity import ComplexityChecker
from sherlock.file_utils import INCLUDE_EXT


DIRECTORY_TYPE = "Directory"
RESOURCE_TYPE = "Resource"
LIBRARY_TYPE = "Library"
SUITE_TYPE = "Suite"


class KeywordStats:
    def __init__(self, name, parent, node=None):
        self.name = name
        self.parent = parent
        self.used = 0
        self.node = node
        self.complexity = self.get_complexity()
        self.timings = KeywordTimings()

    @property
    def status(self):
        # TODO fail (fail), warning statuses (skip)
        if not self.used:
            return "label"
        return "pass"

    def __str__(self):
        # TODO reduce since resource prints table now
        s = f"{self.name}\n"
        s += f"  Used: {self.used}\n"
        if self.complexity:
            s += f"  Complexity: {self.complexity}\n"
        if self.used:
            s += "  Elapsed time:\n"
            s += textwrap.indent(str(self.timings), "    ")
        return s

    def get_complexity(self):
        if not self.node:
            return None
        checker = ComplexityChecker()
        checker.visit(self.node)
        return checker.complexity()


class KeywordTimings:
    def __init__(self):
        self._max = 0
        self._min = math.inf
        self._avg = 0
        self._total = 0
        self._count = 0

    def add_timing(self, elapsed):
        self._count += 1
        self._max = max(self._max, elapsed)
        self._min = min(self._min, elapsed)
        self._total += elapsed
        self._avg = math.floor(self._total / self._count)

    def format_time(self, milliseconds):
        if not self._count:
            return "0"
        seconds = milliseconds / 1000
        return str(round(seconds))

    @property
    def max(self):
        return self.format_time(self._max)

    @max.setter
    def max(self, value):
        self._max = value

    @property
    def min(self):
        return self.format_time(self._min)

    @min.setter
    def min(self, value):
        self._min = value

    @property
    def avg(self):
        return self.format_time(self._avg)

    @avg.setter
    def avg(self, value):
        self._avg = value

    @property
    def total(self):
        return self.format_time(self._total)

    @total.setter
    def total(self, value):
        self._total = value

    def __add__(self, other):
        timing = KeywordTimings()
        timing.max = self._max
        timing.min = self._min
        timing._count = self._count
        timing.avg = self._avg
        timing.total = self._total

        if other._count:
            timing.add_timing(other._total)
        return timing

    def __radd__(self, other):
        return self.__add__(other)


class ResourceVisitor(ast.NodeVisitor):
    def __init__(self, parent):
        self.parent = parent
        self.normal_keywords = NormalizedDict(ignore="_")
        self.embedded_keywords = dict()
        self.variables = Variables()
        self.resources = []
        self.libraries = dict()
        self.has_tests = False

    def visit_TestCase(self, node):  # noqa
        self.has_tests = True

    def visit_Keyword(self, node):  # noqa
        embedded = EmbeddedArguments(node.name)
        if embedded:
            self.embedded_keywords[node.name] = (KeywordStats(node.name, parent=self.parent, node=node), embedded.name)
        else:
            self.normal_keywords[node.name] = KeywordStats(
                node.name, parent=self.parent, node=node
            )  # TODO: handle duplications

    def visit_ResourceImport(self, node):  # noqa
        if node.name:
            self.resources.append(node.name)

    def visit_LibraryImport(self, node):  # noqa
        if node.name:
            self.libraries[(node.name, node.alias)] = node.args

    def visit_Variable(self, node):  # noqa
        if not node.name or node.errors:
            return
        if node.name[0] == "$":
            self.variables[node.name] = node.value[0] if node.value else ""
        elif node.name[0] == "@":
            self.variables[node.name] = list(node.value)
        elif node.name[0] == "&":
            self.variables[node.name] = self.set_dict(node.value)

    @staticmethod
    def set_dict(values):
        ret = {}
        for value in values:
            key, val = value.split("=") if "=" in value else (value, "")
            ret[key] = val
        return ret


class KeywordStore:
    def __init__(self, normal, embedded):
        self._normal = normal
        self._embedded = embedded

    def __iter__(self):
        yield from self._normal.values()
        for kw_stat, pattern in self._embedded.values():
            yield kw_stat

    def find_kw(self, kw_name):
        found = []
        try:
            kw_stat = self._normal[kw_name]
            found.append(kw_stat)
        except KeyError:
            for name, (kw_stat, template) in self._embedded.items():
                if self.match_embedded(kw_name, template):
                    found.append(kw_stat)
        return found

    @staticmethod
    def match_embedded(name, pattern):
        raise NotImplemented


class KeywordLibraryStore(KeywordStore):
    def __init__(self, test_library, parent):
        normal = NormalizedDict(ignore="_")
        for kw in test_library.handlers._normal:
            normal[kw] = KeywordStats(kw, parent=parent)
        embedded = {handler.name: (KeywordStats(handler.name, handler)) for handler in test_library.handlers._embedded}
        super().__init__(normal, embedded)

    @staticmethod
    def match_embedded(name, pattern):
        return pattern.matches(name)


class KeywordResourceStore(KeywordStore):
    def __init__(self, normal, embedded, parent):
        keyword_stats = {name: KeywordStats(name, parent) for name in normal.values()}
        for kw_stat, pattern in embedded.values():
            keyword_stats[kw_stat.name] = kw_stat
        super().__init__(normal, embedded)

    @staticmethod
    def match_embedded(name, pattern):
        return pattern.match(name)


class File:
    def __init__(self, path):
        self.path = path
        self.name = str(Path(path).name)
        self.name_no_ext = str(Path(path).stem)
        self.keywords = []
        self.errors = set()

    def get_resources(self):
        return str(self.path), self

    def get_type(self):
        raise NotImplemented

    def __str__(self):
        s = f"{self.get_type()}: {self.name}\n"
        if self.errors:
            s += "Import errors:\n"
            s += textwrap.indent("".join(self.errors), "    ")
        return s


class Library(File):
    def __init__(self, path):
        super().__init__(path)
        self.type = LIBRARY_TYPE
        self.loaded = False
        self.filter_not_used = False
        self.builtin = False

    def get_type(self):
        return self.type

    def load_library(self, args=None, scope_variables=None):
        if self.keywords:
            return
        # TODO handle exceptions (not enough args etc)
        error = False
        if scope_variables is not None and args:
            replaced_args = []
            for arg in args:
                try:
                    replaced_args.append(scope_variables.replace_string(arg))
                except robot.errors.VariableError as err:
                    error = True
                    self.errors.add(
                        f"Failed to load library with an error: {err} You can provide Robot variables "
                        f"to Sherlock using -v/--variable name:value cli option.\n"
                    )
        else:
            replaced_args = args
        if error:
            return
        name = str(self.path)
        library = TestLibrary(name, replaced_args)
        self.name = library.orig_name
        self.keywords = KeywordLibraryStore(library, name)

    def search(self, name):
        if not self.keywords:
            return []
        return self.keywords.find_kw(name)


class Resource(File):
    def __init__(self, path: Path):
        super().__init__(path)
        self.type = RESOURCE_TYPE
        self.name = path.name  # TODO Resolve chaos with names and paths
        self.directory = str(path.parent)

        model = get_model(str(path), data_only=True, curdir=str(path.cwd()))
        visitor = ResourceVisitor(str(path))
        visitor.visit(model)
        self.keywords = KeywordResourceStore(visitor.normal_keywords, visitor.embedded_keywords, str(path))
        self.has_tests = visitor.has_tests
        self.variables = visitor.variables
        self.current_variables = None

        self.resources = visitor.resources
        self.libraries = visitor.libraries

    def get_type(self):
        return SUITE_TYPE if self.has_tests else RESOURCE_TYPE

    def search(self, name, lib_name):
        if lib_name and lib_name != self.name_no_ext:
            return []
        return self.keywords.find_kw(name)


class Tree:
    def __init__(self, name):
        self.name = name
        self.type = DIRECTORY_TYPE
        self.path = ""
        self.errors = set()
        self.children = []

    @classmethod
    def from_directory(cls, path: Path, gitignore: Optional[PathSpec] = None):
        tree = cls(str(path.name))
        tree.path = path

        for child in path.iterdir():
            gitignore_pattern = f"{child}/" if child.is_dir() else str(child)
            if gitignore is not None and gitignore.match_file(gitignore_pattern):
                continue
            child = child.resolve()
            if child.is_dir():
                library_init = Library(child) if tree.has_init(child) else None

                child_tree = cls.from_directory(path=child, gitignore=gitignore)
                if child_tree.children:  # if the directory is empty (no libraries or resources) skip it
                    if library_init:
                        child_tree.children.append(library_init)
                    tree.children.append(child_tree)
                elif library_init:
                    tree.children.append(library_init)
            elif child.is_file():
                if child.suffix not in INCLUDE_EXT or child.name == "__init__.py":
                    continue
                if child.suffix == ".py":  # TODO better mapping
                    tree.children.append(Library(child))
                else:
                    tree.children.append(Resource(child))
        return tree

    @staticmethod
    def has_init(directory):
        return any(child.name == "__init__.py" for child in directory.iterdir())  # FIXME

    def get_type(self):
        return self.type

    def get_resources(self):
        for resource in self.children:
            if resource.type == DIRECTORY_TYPE:
                yield from resource.get_resources()
            else:
                yield resource.get_resources()

    def __str__(self):
        return f"Directory: {self.name}"
