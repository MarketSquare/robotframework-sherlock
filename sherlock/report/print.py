import textwrap

from sherlock.model import DIRECTORY_TYPE


def log_directory(directory, log_handle, indent=""):
    print(textwrap.indent(str(directory), indent), file=log_handle)
    indent += "    "
    for resource in directory.children:
        if resource.type == DIRECTORY_TYPE:
            log_directory(resource, log_handle, indent)
        else:
            print(textwrap.indent(str(resource), indent), file=log_handle)


def print_report(directory, log_handle):
    print("", file=log_handle)
    log_directory(directory, log_handle)
