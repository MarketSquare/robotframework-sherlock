*** Settings ***
Library  Library.py
Library  Library.py  WITH NAME  Aliased


*** Test Cases ***
Test
    Library.Keyword 1
    Aliased.Keyword 1
