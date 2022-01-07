*** Keywords ***
Suite Keyword
    FOR  ${var}  IN RANGE  2
        Other Keyword
    END
    [Teardown]    Other Keyword

Other Keyword
    Log  Here I Am!
