import argparse
from typing import List
from pathlib import Path

import toml
from robot.conf import RobotSettings

from sherlock.file_utils import find_project_root, find_file_in_project_root, get_gitignore
from sherlock.exceptions import SherlockFatalError
from sherlock.version import __version__


BUILT_IN = "BuiltIn"
ROBOT_DEFAULT_OUTPUT = "output.xml"


class CommaSeparated(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.split(","))


class Config:
    def __init__(self, from_cli=True):
        self.path = Path.cwd()
        self.output = None
        self.log_output = None
        self.report: List[str] = ["print"]
        self.variable = []
        self.variablefile = []
        self.robot_settings = None
        self.include_builtin = False
        self.root = Path.cwd()
        self.default_gitignore = None
        self.resource: List[str] = []
        if from_cli:
            self.parse_cli()
        self.init_variables()

    def parse_cli(self):
        parser = self._create_parser()
        parsed_args = parser.parse_args()

        self.set_root(parsed_args)

        default = self.get_defaults_from_config(parsed_args)
        if default:
            # set only options not already set from cli
            self.set_parsed_opts(default)

        self.set_parsed_opts(dict(**vars(parsed_args)))
        self.validate_output()
        self.validate_report()

    def validate_output(self):
        if self.output is None:
            output = (self.path if self.path.is_dir() else self.path.parent) / ROBOT_DEFAULT_OUTPUT
            if output.is_file():  # TODO document this
                self.output = output
        elif not self.output.is_file():
            raise SherlockFatalError(
                f"Reading Robot Framework output file failed. No such file: '{self.output}'"
            ) from None

    def validate_report(self):
        if not self.report:
            return
        allowed = ("print", "html", "json")
        for report in self.report:
            if report not in allowed:
                raise SherlockFatalError(
                    f"Report '{report}' not recognized. "
                    f"Use comma separated list of values from: {', '.join(allowed)}"
                )

    def set_root(self, parsed_args):
        self.root = find_project_root((getattr(parsed_args, "path", Path.cwd()),))
        if self.root:
            self.default_gitignore = get_gitignore(self.root)

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="sherlock",
            description=f"Code complexity analyser for Robot Framework. Version: {__version__}\n",
            argument_default=argparse.SUPPRESS,
        )

        parser.add_argument(
            "path", metavar="SOURCE", default=self.path, nargs="?", type=Path, help="Path to source code"
        )
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            help="Path to Robot Framework output file",
        )
        parser.add_argument(
            "-r", "--resource", action="append", help="Path/name of the library or resource to be included in analysis"
        )
        parser.add_argument(
            "-rp",
            "--report",
            action=CommaSeparated,
            help="Generate reports after analysis. Use comma separated list for multiple reports. "
            "Available reports: print (default), html, json",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Path to TOML configuration file",
        )
        parser.add_argument(
            "-v", "--variable", help="Set Robot variable in Sherlock namespace", metavar="name:value", action="append"
        )
        parser.add_argument(
            "-V",
            "--variablefile",
            help="Set Robot variable in Sherlock namespace from Python or YAML file",
            metavar="path",
            action="append",
        )
        parser.add_argument(
            "--include-builtin",
            help="Use this flag to include BuiltIn libraries in analysis",
            action="store_true",
        )
        parser.add_argument(
            "--log-output",
            type=argparse.FileType("w"),
            help="Path to output log",
        )
        return parser

    def set_parsed_opts(self, namespace):
        for key, value in namespace.items():
            if key in self.__dict__:
                self.__dict__[key] = value

    def get_defaults_from_config(self, parsed_args):
        if "config" in parsed_args:
            config_path = parsed_args.config
            if not Path(config_path).is_file():
                raise SherlockFatalError(f"Configuration file '{config_path}' does not exist") from None
        else:
            config_path = find_file_in_project_root("pyproject.toml", self.root)
            if not config_path.is_file():
                return {}
        return TomlConfigParser(config_path=config_path, look_up=self.__dict__).get_config()

    def init_variables(self):
        self.robot_settings = RobotSettings({"variable": self.variable, "variablefile": self.variablefile})


class TomlConfigParser:
    def __init__(self, config_path, look_up):
        self.config_path = str(config_path)
        self.look_up = look_up

    def read_from_file(self):
        try:
            config = toml.load(self.config_path)
        except toml.TomlDecodeError as err:
            raise SherlockFatalError(f"Failed to decode {self.config_path}: {err}") from None
        return config.get("tool", {}).get("sherlock", {})

    def get_config(self):
        read_config = {}
        config = self.read_from_file()
        if not config:
            return read_config

        toml_data = {key.replace("-", "_"): value for key, value in config.items()}
        for key, value in toml_data.items():
            if key == "log_output":
                read_config[key] = argparse.FileType("w")(value)
            elif key == "report":
                read_config[key] = value.split(",") if isinstance(value, str) else value
            elif key == "config":
                raise SherlockFatalError("Nesting configuration files is not allowed")
            elif key == "output":
                read_config[key] = Path(value)
            elif key == "include_builtin":
                read_config[key] = str(value).lower() in ("true", "1", "yes", "t", "y")  # TODO tests
            elif key in self.look_up:
                read_config[key] = value
            else:
                raise SherlockFatalError(f"Option '{key}' is not supported in configuration file")
        return read_config
