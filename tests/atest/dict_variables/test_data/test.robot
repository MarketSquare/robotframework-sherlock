*** Variables ***
&{DICT VAR}    key=value
...    key2=value
@{LIST}    1  2  3
${VAR}    ENV
${VAR2}    ENV2  # comment
VAR  3
&{CONTAINS_OTHER}    &{MANY}
&{INVALID}    key
&{EQUAL_SIGN}=    key=string with = sign
&{EQUAL_SIGN} =    key=string with = sign
&{EMPTY}

*** Test Cases ***
Test
    Keyword 1

*** Keywords ***
Keyword 1
    No Operation
