*** Keywords ***
Keyword 1
    Log  1

Keyword 2
    Keyword 3

Keyword 3
    Log  3
    No Operation
    ${condition}    Set Variable  ${True}
    IF  ${condition}
        IF  ${condition}
            Should Be True  ${True}
        ELSE IF  False
            Should Be False  ${False}
        END
    END
    IF  ${condition}
        IF  ${condition}
            Should Be True  ${True}
        ELSE IF  False
            Should Be False  ${False}
        END
    END

Keyword 4
    Log  4

Run Keyword With ${variable}
    Log    ${variable}
