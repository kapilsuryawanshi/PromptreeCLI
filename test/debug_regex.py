#!/usr/bin/env python3
"""
Debug the regex patterns for edit command
"""

import re

def test_regex_patterns():
    """Test the regex patterns used in the edit command"""
    
    # Pattern for editing subject
    subject_pattern = r'^(\\d+)\\s+-subject\\s+\"(.+)\"$'
    # Pattern for editing parent
    parent_pattern = r'^(\\d+)\\s+-parent\\s+(\\d+|None|none|null|NULL)$'
    
    test_cases = [
        '2 -subject "Updated Child Subject"',
        '2 -subject "Test"',
        '2 -parent None',
        '2 -parent 1',
        '2 -parent null',
        '2 -parent none',
        'invalid input',
        '2 -other "test"'
    ]
    
    print("Testing regex patterns:")
    for test_case in test_cases:
        print(f"\nTesting: {test_case!r}")
        
        subject_match = re.match(subject_pattern, test_case, re.DOTALL)
        parent_match = re.match(parent_pattern, test_case.strip())
        
        print(f"  Subject match: {subject_match.groups() if subject_match else 'No match'}")
        print(f"  Parent match: {parent_match.groups() if parent_match else 'No match'}")

if __name__ == "__main__":
    test_regex_patterns()