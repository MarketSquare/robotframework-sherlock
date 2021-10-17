*** Settings ***
Resource  ..${/}resources${/}resourceA.resource
Resource  ..${/}resources${/}resourceB.robot  # keyword 4 redefined
Library   ..${/}libs${/}MyPythonLibrary.py    test


*** Test Cases ***
Test A
    Keyword 1
    Keyword 2
    Keyword 4

Test B
    Keyword 1
    Keyword 4

Test C
    Python Keyword  a
    #  Python Keyword  call without args etc?

Test Embedded
    Run Keyword With abcd
    Run Keyword With 1
    run keyword with abc
