import importlib.util
import inspect
from pathlib import Path

import sherlock.exceptions


class Report:
    def get_report(self, tree, tree_name, path_root):
        raise NotImplementedError


def _import_module_from_file(file_path):
    """Import Python file as module.

    importlib does not support importing Python files directly, and we need to create module specification first."""
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def modules_from_paths(paths, recursive=True):
    for path in paths:
        path_object = Path(path)
        if path_object.is_dir():
            if not recursive or path_object.name in {".git", "__pycache__"}:
                continue
            yield from modules_from_paths([file for file in path_object.iterdir()])
        elif path_object.suffix == ".py":
            yield _import_module_from_file(path_object)


def load_reports():
    """
    Load all valid reports.
    Report is considered valid if it inherits from `Report` class
    and contains both `name` and `description` attributes.
    """
    reports = {}
    for module in modules_from_paths([Path(__file__).parent]):
        classes = inspect.getmembers(module, inspect.isclass)
        for report_class in classes:
            if not issubclass(report_class[1], Report):
                continue
            report = report_class[1]()
            if not hasattr(report, "name") or not hasattr(report, "description"):
                continue
            reports[report.name] = report
    return reports


def get_reports(configured_reports):
    """
    Returns dictionary with list of valid, enabled reports (listed in `configured_reports` set of str).
    """
    reports = load_reports()
    enabled_reports = {}
    for report in configured_reports:
        if report not in reports:
            raise sherlock.exceptions.InvalidReportName(report, reports)
        elif report not in enabled_reports:
            enabled_reports[report] = reports[report]
    return enabled_reports
