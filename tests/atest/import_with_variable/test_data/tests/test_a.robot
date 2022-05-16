*** Settings ***
Resource  a.resource


*** Variables ***
${VARIABLE}  b

*** Test Cases ***
Test
    Keyword 1


*** Keywords ***
Internal Keyword
    Log  I am called from b.resource
