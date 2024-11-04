

# extract expected test outcome from test file
def expected_output(test_data):
    if test_data is not None and 'tests' in test_data:
        all_expected_outputs = []
        all_tests = [key for key in test_data['tests'].keys()]
        # iterate through each test and run it
        for test_key in all_tests:
            test = test_data['tests'].get(test_key, {})
            expected_output = test.get('expected output', '')  # get the expected output string
            if expected_output:
                all_expected_outputs.append(expected_output)
        output = all_expected_outputs[0]
        return output
    return []