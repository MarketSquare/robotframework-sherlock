*** Settings ***
Library  Library1.py
Library  Library2.py
Resource  test.resource


*** Test Cases ***
Test
    Library1.Keyword 1
    Library2.Keyword 1
    library1.Keyword 1
    FOR  ${i}  IN RANGE  21
        Keyword 1
    END
