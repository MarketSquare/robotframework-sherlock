*** Settings ***
Resource    ..${/}resources${/}test.resource


*** Test Cases ***
Test
    Python Keyword
    Robot Keyword
    FOR  ${a}  IN RANGE  3
        Robot Keyword 2
    END
