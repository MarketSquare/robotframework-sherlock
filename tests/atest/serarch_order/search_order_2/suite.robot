*** Settings ***
Resource    a.resource
Resource    b.resource


*** Test Cases ***
Test
    Keyword


*** Keywords ***
Duplicated
    Log  From suite
