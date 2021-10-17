*** Settings ***
Resource    ..${/}..${/}resources${/}resourceA.resource
Resource    idontexist.resource
Library     ..${/}..${/}libs${/}MyPythonLibrary.py  test  # imported but not used

*** Variables ***
${B}    5

*** Test Cases ***
Test A
    FOR  ${a}  IN RANGE  ${B}
        Keyword 1
        Keyword 2
        Keyword 4
    END
    Internal Keyword

*** Keywords ***
Internal_keyword
    Log  Internal
