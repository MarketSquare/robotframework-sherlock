import textwrap


def log_directory(directory, log_handle, indent=""):
    print(textwrap.indent(str(directory), indent) + "\n", file=log_handle)
    indent += "    "
    for resource in directory.children:
        if resource.type == "Directory":
            log_directory(resource, log_handle, indent)
        else:
            print(textwrap.indent(str(resource), indent) + "\n", file=log_handle)


def print_report(directory, name, log_handle):
    print(name)
    log_directory(directory, log_handle)
