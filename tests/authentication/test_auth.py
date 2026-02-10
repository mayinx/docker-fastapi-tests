import os
import requests
from collections import namedtuple
from typing import NamedTuple

# Constants
API_ADDRESS = os.environ.get("API_ADDRESS", "api")
API_PORT = int(os.environ.get("API_PORT", "8000"))
LOG = os.environ.get('LOG', "0") 

class TestCase(NamedTuple):
    username: str
    password: str
    expected_code: int

# list with test cases to iterate 
test_cases = [
    TestCase("alice", "wonderland", 200),
    TestCase("bob", "builder", 200),
    TestCase("clementine", "mandarine", 403),
]

class TestResult(NamedTuple):
    is_success: bool
    status_code: int
    test_status: str

def check_test_case(test_case: TestCase) -> TestResult:
    r = requests.get(
        url='http://{address}:{port}/permissions'.format(address=API_ADDRESS, port=API_PORT),
        params= {
            'username': test_case.username,
            'password': test_case.password 
        }
    )  

    is_success = r.status_code == test_case.expected_code

    return TestResult(
        is_success=is_success, 
        status_code=r.status_code, 
        test_status="SUCCESS" if is_success else "FAILURE"    
)

def log_result(test_case: TestCase, test_result: TestResult):
    output = f'''
    ============================
        Authentication test
    ============================
    request done at "/permissions"
    | username="{test_case.username}"
    | password="{test_case.password}"
    expected result = {test_case.expected_code}
    actual result = {test_result.status_code}
    ==> TEST STATUS: {test_result.test_status}
    '''

    # write log to console
    print(output)

    # write log to file
    if LOG == "1":
        with open('api_test.log', 'a') as file:
            file.write(output + "\n")    

for test_case in test_cases:
    test_result = check_test_case(test_case)
    log_result(test_case, test_result)
