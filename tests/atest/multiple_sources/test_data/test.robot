*** Settings ***
Resource  resource1${/}file.resource
Resource  resource2${/}file2.resource

*** Test Cases ***
Test
    Keyword 1
    Keyword 2
