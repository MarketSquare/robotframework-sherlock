*** Settings ***
Library    TemplatedData

*** Test Cases ***
Test
    ${data}    Get Templated Data From Path    test_data.txt

Other test
    ${data}    Get Templated Data From Path    test_data.txt
