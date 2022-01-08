import os
from pathlib import Path

from robot.api import SuiteVisitor
from robot.variables import Variables

from sherlock.model import LIBRARY_TYPE


class StructureVisitor(SuiteVisitor):
    def __init__(self, resources, from_output):
        self.resources = resources
        self.from_output = from_output
        self.variables = Variables()
        self.variables["${/}"] = os.path.sep

        self.search_scope = None
        self.suite_errors = set()
        self.errors = []

    def get_local_variables(self, suite):
        variables = Variables()
        variables.update(self.variables)

        for variable in suite.resource.variables:
            variables[variable.name] = variable.value[0]  # TODO scalars
        variables["${CURDIR}"] = Path(suite.resource.source).parent

        return variables

    def visit_suite(self, suite):
        self.suite_errors = set()
        self.search_scope = None
        # TODO set them from --variables and such
        if hasattr(suite, "resource"):
            self.search_scope = suite.resource.source
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
                if imported.type == LIBRARY_TYPE:
                    self.resources[name].load_library(imported.args)
        else:
            # handle libname (such as resourceA) with accordance to possible paths
            if suite.source in self.resources:
                self.search_scope = suite.source
            elif Path(suite.source).is_dir() and str(Path(suite.source) / "__init__.robot") in self.resources:
                self.search_scope = str(Path(suite.source) / "__init__.robot")

        suite.setup.visit(self)
        suite.tests.visit(self)
        suite.teardown.visit(self)

        # TODO improve error handling
        if self.suite_errors:
            self.errors.append(f"\nErrors in {suite.source}:")
        self.errors.extend(list(self.suite_errors))

        suite.suites.visit(self)

    def visit_keyword(self, kw):
        if self.search_scope is None:
            return
        name = kw.kwname if self.from_output else kw.name
        libname = kw.libname if self.from_output else None
        found = self.resources[self.search_scope].search(name, self.resources, libname)
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
