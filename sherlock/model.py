import ast
import os
import textwrap
import math
from pathlib import Path
from typing import Optional

import robot.errors
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
            s += "  Timings:\n"
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
            return "00:00:00:00"
        hours, milliseconds = divmod(milliseconds, 360000)
        minutes, milliseconds = divmod(milliseconds, 60000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

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

    def __str__(self):
        cols = [[self.total, self.min, self.max, self.avg]]
        headers = ["Total elapsed", "Shortest execution", "Longest execution", "Average execution"]
        return tabulate(cols, headers=headers, tablefmt="plain") + "\n"


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
        if node.name:
            self.variables[node.name] = node.value[0]  # FIXME arrays and such..by default ${VAR}  1 -> 1 is tuple


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


def _normalize_library_path(library):
    path = library.replace("/", os.sep)
    if os.path.exists(path):
        return os.path.abspath(path)
    return library


def _get_library_name(name, directory):
    if not _is_library_by_path(name):
        return name
    return find_file(name, directory, LIBRARY_TYPE)  # TODO handle DataError when not found


def _is_library_by_path(path):
    return path.lower().endswith((".py", "/", os.sep))


class File:
    def __init__(self, path):
        self.path = path
        self.name = str(Path(path).name)
        self.keywords = None
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
        if not self.keywords:
            return s
        keywords = [kw for kw in self.keywords]
        if keywords:
            timings = sum((kw.timings for kw in keywords if kw.used), KeywordTimings())
            s += "  Timings:\n"
            s += textwrap.indent(str(timings), "    ")
            s += f"\n  Keywords:\n"
            # FIXME Timings (and are optional too)
            has_complexity = any(kw.complexity for kw in keywords)
            kw_table = []
            for kw in keywords:
                row = [kw.name, kw.used]
                if has_complexity:
                    row.append(kw.complexity)
                row.append(kw.timings.total if kw.used else "")
                kw_table.append(row)
            headers = ["Keyword", "Executions"]
            if has_complexity:
                headers.append("Complexity")
            headers.append("Elapsed")
            table = tabulate(kw_table, headers=headers, tablefmt="pretty", colalign=("left",))
            s += textwrap.indent(table, "    ")
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

    def search(self, name, *args):
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
        self.imported_resources, self.imported_libraries = [], []

    def get_type(self):
        return SUITE_TYPE if self.has_tests else RESOURCE_TYPE

    def init_imports(self, namespace):
        """Called on start of every suite to resolve imports"""
        self.imported_resources, self.imported_libraries = [], []

        self.current_variables = Variables()
        self.current_variables.update(namespace if hasattr(namespace, "store") else namespace.current)  # FIXME
        self.current_variables.update(self.variables.copy())

        for resource in self.resources:
            try:
                resource = self.current_variables.replace_string(resource)
            except DataError as err:
                pass
                # TODO
                # self._raise_replacing_vars_failed(import_setting, err)
            self.imported_resources.append(str(Path(self.directory, resource).resolve()))  # FIXME
        for (lib, alias), args in self.libraries.items():
            library = self.current_variables.replace_string(lib)
            library = _normalize_library_path(library)
            library = _get_library_name(library, self.directory)
            self.imported_libraries.append((library, alias, args))

    def search(self, name, resources, libname):
        found = []
        if not libname or Path(self.path).stem == libname:
            found += self.keywords.find_kw(name)
            if found:
                return found
        for resource in self.imported_resources:
            if resource in resources:
                resources[resource].init_imports(self.current_variables)
                found += resources[resource].search(name, resources, libname)
                if found:
                    return found
        for lib, alias, args in self.imported_libraries:
            if lib not in resources:
                continue
            resources[lib].load_library(args, self.current_variables)
            if not libname or (alias and alias == libname) or (not alias and resources[lib].name == libname):
                found += resources[lib].search(name, resources)
        if found:
            return found
        return resources["BuiltIn"].search(name, resources)


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
                # TODO check if __init__ inside
                if tree.has_init(child):
                    tree.children.append(Library(child))
                child_tree = cls.from_directory(path=child, gitignore=gitignore)
                if child_tree.children:  # if the directory is empty (no libraries or resources) skip it
                    tree.children.append(child_tree)
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
