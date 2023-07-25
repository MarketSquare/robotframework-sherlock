*** Settings ***
Library    IDontExist.py
Library    LibraryWithArgs.py  # missing required arg
Library    Library.py    arg  # library that does not have arguments
Library     LibraryWithFailingInit.py


*** Test Cases ***
Test
    Keyword 1

*** Keywords ***
Keyword 1
    No Operation
