*** Settings ***
Library  ${library}.py  ${VARIABLE}


*** Variables ***
${LIBRARY}     Library1
${VARIABLE}    ${LIBRARY}

*** Test Cases ***
Test
    Keyword 1
