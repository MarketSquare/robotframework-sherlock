# Sherlock
The tool for analyzing Robot Framework code in terms of not used code, code complexity or performance issues.

The tool is in the alpha state. If you find anything unexpected, or you have idea for improvements 
not listed in Github issues already please open an issue.

## Installation
You can install Sherlock by running in the root of the project:
```commandline
pip install -e .
```

## Usage

Run with:
```commandline
sherlock --output-path <path to output.xml file> <path to source code repository>
```

To analyze external library/resource use ``--resource`` option:
```commandline
sherlock --output-path output.xml --resource SeleniumLibrary src/
```
```commandline
sherlock --output-path output.xml --resource external_repository_used_in_tests/ src/
```

## Reports
Sherlock by default prints the output. You can configure what reports are produced by sherlock using ``--report`` option:
```commandline
sherlock --report print
```
```commandline
sherlock --report html
```
``--report`` accepts comma separated list of reports:
```commandline
sherlock --report print,html,json
```

## BuiltIn library

To show analysis of BuiltIn libraries use ``--include-builtin`` flag:
```commandline
sherlock --include-builtin src/
```
