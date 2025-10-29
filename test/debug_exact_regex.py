#!/usr/bin/env python3
"""
Test the exact regex patterns from the file
"""

import re

def test_exact_patterns():
    """Test the exact regex patterns from the file"""
    
    # These are the exact patterns from the file (before Python processes them)
    # In Python source, we write r'^(\\d+)...' to get ^(\\d+)... after raw string processing
    # which results in ^(\d+)... for the actual regex engine
    subject_pattern = r'^(\\d+)\\s+-subject\\s+"(.+)"$'
    parent_pattern = r'^(\\d+)\\s+-parent\\s+(\\d+|None|none|null|NULL)$'
    
    test_cases = [
        '2 -subject "Updated Child Subject"',
        '2 -subject "Test"',
        '2 -parent None',
        '2 -parent 1',
        '2 -parent null',
        '2 -parent none',
    ]
    
    print("Testing EXACT patterns from file:")
    print(f"Subject pattern: {subject_pattern}")
    print(f"Parent pattern: {parent_pattern}")
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case!r}")
        
        subject_match = re.match(subject_pattern, test_case, re.DOTALL)
        parent_match = re.match(parent_pattern, test_case.strip())
        
        print(f"  Subject match: {subject_match.groups() if subject_match else 'No match'}")
        print(f"  Parent match: {parent_match.groups() if parent_match else 'No match'}")

if __name__ == "__main__":
    test_exact_patterns()