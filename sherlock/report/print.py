from rich.console import Console, Group
from rich.markup import escape
from rich.text import Text
from rich.tree import Tree
from rich.table import Table


from sherlock.model import DIRECTORY_TYPE
from sherlock.model import KeywordTimings


def timings_to_table(timings):
    timings_table = Table(title="Elapsed time")
    for col in ["Total elapsed [s]", "Shortest execution [s]", "Longest execution [s]", "Average execution [s]"]:
        timings_table.add_column(col)
    timings_table.add_row(timings.total, timings.min, timings.max, timings.avg)
    return timings_table


def keywords_to_table(keywords):
    has_complexity = any(kw.complexity for kw in keywords)
    table = Table(title="Keywords:")
    table.add_column("Name", justify="left", no_wrap=True)
    table.add_column("Executions")
    if has_complexity:
        table.add_column("Complexity")
    table.add_column("Average time [s]")
    table.add_column("Total time [s]")
    for kw in keywords:
        name = kw.name if kw.used else f"[cyan]{kw.name}"
        row = [name, str(kw.used)]
        if has_complexity:
            row.append(str(kw.complexity))
        if kw.used:
            row.extend([str(kw.timings.avg), str(kw.timings.total)])
        else:
            row.extend(["", ""])
        table.add_row(*row)
    return table


def log_directory(directory, tree):
    for resource in directory.children:
        if resource.type == DIRECTORY_TYPE:
            style = "dim" if resource.name.startswith("__") else ""
            branch = tree.add(
                f"[bold magenta][link file://{resource.name}]{escape(resource.name)}",
                style=style,
                guide_style=style,
            )
            log_directory(resource, branch)
        else:
            text = Text(str(resource))
            keywords = [kw for kw in resource.keywords]
            if keywords:
                timings = sum((kw.timings for kw in keywords if kw.used), KeywordTimings())
                timings_table = timings_to_table(timings)
                keywords_table = keywords_to_table(keywords)

                tree.add(Group(text, timings_table, keywords_table))
            else:
                tree.add(text)


def print_report(directory, log_handle):
    tree = Tree(
        f"[link file://{directory}]{directory}",
        guide_style="bold bright_blue",
    )
    log_directory(directory, tree)
    console = Console()
    console.print()
    console.print(tree)
