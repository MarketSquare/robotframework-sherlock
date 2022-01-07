*** Settings ***
Resource          resource.robot
Suite Setup       Suite Keyword
Suite Teardown    Suite Keyword

*** Test Cases ***
Empty Test
    [Teardown]    Internal Keyword
    No Operation


*** Keywords ***
Internal Keyword
    No Operation
