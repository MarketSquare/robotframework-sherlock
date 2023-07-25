*** Settings ***
Suite Setup    Run Keyword    keyword 1
Suite Teardown    Run Keywords    Keyword 1    AND    Keyword 2


*** Test Cases ***
Test
    Run Keyword If    ${TRUE}    Keyword 1
    Run Keyword And Ignore Error    Keyword 3

*** Keywords ***
Keyword 1
    No Operation

Keyword 2
    Keyword 1

Keyword 3
    No Operation
