*** Settings ***
Library  Library1.py
Library  Library2.py


*** Test Cases ***
Test
    Library1.Keyword 1
    Library2.Keyword 1
    library1.Keyword 1
