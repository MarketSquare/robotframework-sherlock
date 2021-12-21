import argparse
from typing import List
from pathlib import Path

import toml

from sherlock.file_utils import find_project_root, find_file_in_project_root
from sherlock.exceptions import SherlockFatalError


class CommaSeparated(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.split(","))


class Config:
    def __init__(self, from_cli=True):
        self.path = None
        self.output_path = None
        self.log_output = None
        self.report: List[str] = ["print"]
        self.root = Path.cwd()
        if from_cli:
            self.parse_cli()

    def parse_cli(self):
        parser = self._create_parser()
        parsed_args = parser.parse_args()

        self.set_root(parsed_args)

        default = self.get_defaults_from_config(parsed_args)
        if default:
            # set only options not already set from cli
            self.set_parsed_opts(default)

        self.set_parsed_opts(dict(**vars(parsed_args)))

    def set_root(self, parsed_args):
        self.root = find_project_root((getattr(parsed_args, "path", Path.cwd()),))  # TODO make iterable

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="sherlock",
            description="Code complexity analyser for Robot Framework.\n",
            argument_default=argparse.SUPPRESS,
        )

        parser.add_argument("path", metavar="SOURCE", default=self.path, type=Path, help="Path to source code")
        parser.add_argument(
            "--output-path",
            type=Path,
            help="Path to Robot Framework output file",
        )
        parser.add_argument(
            "--log-output",
            type=argparse.FileType("w"),
            help="Path to output log",
        )
        parser.add_argument(
            "--report",
            action=CommaSeparated,
            help="Report types",
        )
        parser.add_argument(
            "--config",
            help="Path to TOML configuration file",
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
            elif key == "output_path":
                read_config[key] = Path(value)
            elif key in self.look_up:
                read_config[key] = value
            else:
                raise SherlockFatalError(f"Option '{key}' is not supported in configuration file")
        return read_config
