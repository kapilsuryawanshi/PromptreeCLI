#!/usr/bin/env python3
"""
Debug the argument parsing for the edit command
"""

import shlex

def test_parsing():
    test_cases = [
        '2 -parent None -subject "Hello World"',
        '2 -subject "Hello World" -parent 3',
        '2 -parent None',
        '2 -parent 3',
        '2 -subject "Hello World"'
    ]
    
    for test_cmd in test_cases:
        print(f"\nTesting: {test_cmd}")
        try:
            tokens = shlex.split(test_cmd)
            print(f"  Tokens: {tokens}")
            
            # Simulate the parsing logic
            conv_id = int(tokens[0])
            print(f"  Conv ID: {conv_id}")
            
            new_subject = None
            new_parent_id = None
            i = 1
            while i < len(tokens):
                print(f"    Processing token: {tokens[i]}")
                if tokens[i] == '-subject' and i + 1 < len(tokens):
                    new_subject = tokens[i + 1]
                    print(f"      Set new_subject to: {new_subject!r}")
                    i += 2
                elif tokens[i] == '-parent' and i + 1 < len(tokens):
                    parent_arg = tokens[i + 1]
                    print(f"      Processing parent_arg: {parent_arg!r}")
                    if parent_arg.lower() in ['none', 'null']:
                        new_parent_id = None
                        print(f"      Set new_parent_id to: None")
                    else:
                        new_parent_id = int(parent_arg)
                        print(f"      Set new_parent_id to: {new_parent_id}")
                    i += 2
                else:
                    print(f"      Unexpected token: {tokens[i]}")
                    i += 1
            
            print(f"  Final: new_subject={new_subject!r}, new_parent_id={new_parent_id!r}")
            
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_parsing()