*** Variables ***
&{DICT VAR}    key=value
...    key2=value
@{LIST}    1  2  3
${VAR}    ENV
${VAR2}    ENV2  # comment
VAR  3
&{CONTAINS_OTHER}    &{MANY}
&{INVALID}    key
&{EMPTY}

*** Test Cases ***
Test
    Keyword 1

*** Keywords ***
Keyword 1
    No Operation
