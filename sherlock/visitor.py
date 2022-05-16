from collections import OrderedDict
import os
from pathlib import Path

from sherlock.model import LIBRARY_TYPE

from robot.api import SuiteVisitor
from robot.variables.scopes import VariableScopes
from robot.utils import NormalizedDict, find_file
from robot.variables.variables import Variables
from robot.errors import DataError


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


class StructureVisitor(SuiteVisitor):
    def __init__(self, resources, from_output, robot_settings):
        self.resources = resources
        self.from_output = from_output
        self.variables = VariableScopes(robot_settings)
        self.suite_resource = None
        self.imported_resources = OrderedDict()
        self.imported_libraries = OrderedDict()

        self.suite_errors = set()
        self.errors = []

    def init_imports(self, resource, variables=None):
        # TODO read variables from suite and add it to self.variables
        current_variables = Variables()
        # global vars
        current_variables.update(
            self.variables if hasattr(self.variables, "store") else self.variables.current
        )  # FIXME
        # resource vars
        current_variables.update(resource.variables.copy())
        # vars from resources importing given resource
        if variables:
            current_variables.update(variables.copy())
        for res in resource.resources:
            try:
                res = current_variables.replace_string(res)
            except DataError as err:
                pass
                # TODO
                # self._raise_replacing_vars_failed(import_setting, err)
            res = str(Path(resource.directory, res).resolve())  # FIXME
            if res in self.resources and res not in self.imported_resources:
                self.imported_resources[res] = self.resources[res]
                self.init_imports(self.resources[res], current_variables)

        for (lib, alias), args in resource.libraries.items():
            library = current_variables.replace_string(lib)
            library = _normalize_library_path(library)
            library = _get_library_name(library, resource.directory)
            if library in self.resources:
                self.resources[library].load_library(args, current_variables)
                lib_name = alias or self.resources[library].name
                self.imported_libraries[lib_name] = self.resources[library]

    def visit_suite(self, suite):
        self.imported_resources = OrderedDict()
        self.imported_libraries = OrderedDict()
        if suite.source in self.resources:
            suite_resource = self.resources[suite.source]
        elif Path(suite.source).is_dir() and str(Path(suite.source) / "__init__.robot") in self.resources:
            suite_resource = self.resources[str(Path(suite.source) / "__init__.robot")]
        else:
            suite_resource = ""
            # raise SherlockFatalError(f"Could not find definition of '{suite.source}' suite")  # TODO
        if suite_resource:
            self.suite_resource = suite_resource
            self.init_imports(suite_resource)
        suite.setup.visit(self)
        suite.tests.visit(self)

        # TODO improve error handling
        # if self.suite_errors:
        #     self.errors.append(f"\nErrors in {suite.source}:")
        # self.errors.extend(list(self.suite_errors))

        suite.teardown.visit(self)
        suite.suites.visit(self)

    def visit_keyword(self, kw):
        name = kw.kwname if self.from_output else kw.name
        lib_name = kw.libname if self.from_output else None
        found = self.search_def(name, lib_name)
        if not found:
            self.suite_errors.add(f"Keyword '{name}' definition not found")
        elif len(found) > 1:
            s = f"Keyword '{name}' matches following resources/libraries:\n"
            self.suite_errors.add(s)
        else:
            found[0].used += 1
            if self.from_output:
                found[0].timings.add_timing(kw.elapsedtime)
            if hasattr(kw, "body"):
                kw.body.visit(self)
        kw.teardown.visit(self)

    def search_def(self, kw_name, lib_name):
        found = []
        if self.suite_resource:
            found += self.suite_resource.search(kw_name, lib_name)
        if found:
            return found
        for res_name, resource in self.imported_resources.items():
            found += resource.search(kw_name, lib_name)
        if found:
            return found
        for lib_name_or_alias, library in self.imported_libraries.items():
            if lib_name and lib_name != lib_name_or_alias:
                continue
            found += library.search(kw_name)
        if not found:
            return self.resources["BuiltIn"].search(kw_name)
        return found
