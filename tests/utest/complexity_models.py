model_1complexity = """
*** Keywords ***
Keyword
    Keyword Call
    Another Keyword Call
    # Comment
    Keyword With
    ...  ${multiline}
    ...  ${args}

"""

model_3complexity = """
*** Keywords ***
Keyword
    Keyword Call
    Another Keyword Call
    # Comment
    IF  condition
        Keyword Call
    ELSE
        Keyword Call
    END
    Keyword With
    ...  ${multiline}
    ...  ${args}

"""

model_5complexity = """
*** Keywords ***
Keyword
    Keyword Call
    Another Keyword Call
    # Comment
    IF  condition
        Keyword Call
    ELSE
        Keyword Call
        FOR  ${var}  IN RANGE  10
            Log    ${var}
        END
    END
    Keyword With
    ...  ${multiline}
    ...  ${args}

"""
