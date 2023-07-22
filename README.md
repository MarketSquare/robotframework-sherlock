# Sherlock
The tool for analyzing Robot Framework code in terms of not used code, code complexity or performance issues.

> **Note**
> 
> The tool is in the ***Alpha*** state, which means it may be unstable and should be used at your own risk. Some 
> features may be broken and there are still many things to be developed. If you find anything unexpected, or you have ideas for improvements 
> not listed in GitHub issues, please open an new issue.

## Installation

You can install the latest version of Sherlock simply by running:
```commandline
pip install -U robotframework-sherlock
```

Sherlock requires Python 3.8+.

## Usage

Sherlock can prepare analysis based on your source code alone. However, it's currently highly recommended to also include
output of test execution.

Run Sherlock with:
```commandline
sherlock --output <path to output.xml file> <path to source code repository>
```

To analyze external library/resource use ``--resource`` option:
```commandline
sherlock --output output.xml --resource SeleniumLibrary src/
```
```commandline
sherlock --output output.xml --resource external_repository_used_in_tests/ src/
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
