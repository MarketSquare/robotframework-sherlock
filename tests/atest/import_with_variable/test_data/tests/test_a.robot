*** Settings ***
Resource  a.resource


*** Variables ***
${VARIABLE}  b

*** Test Cases ***
Test
    Keyword 1


*** Keywords ***
Internal Keyword
    Log  I should never be called
