import re

# This is exactly what's in the source file (with double backslashes)
# which after Python processes the raw string, becomes single backslashes
# which the regex engine should handle properly
pattern = '^(\\\\d+)\\\\s+-subject\\\\s+\\\"(.+)\\\"$'
print(f"Pattern as stored in variable: {pattern!r}")

# Test it by compiling the actual string
arg = '2 -subject "Updated Child Subject"'
match = re.match(pattern, arg, re.DOTALL)
print(f"Match result: {match}")
if match:
    print(f"Groups: {match.groups()}")
else:
    # Let me try to understand by testing what the raw string actually becomes
    raw_pattern = r'^(\\\\d+)\\\\s+-subject\\\\s+\\\"(.+)\\\"$'
    print(f"Raw string pattern: {raw_pattern!r}")
    match2 = re.match(raw_pattern, arg, re.DOTALL)
    print(f"Match with raw: {match2}")
    if match2:
        print(f"Groups with raw: {match2.groups()}")
    
    # What Python will actually process it to:
    # r'^(\\\\d+)' -> becomes '^(\\d+)' in memory
    # Then regex engine should process this to ^(\d+) which is correct
    
    # Let me try the correct pattern 
    correct_pattern = r'^(\d+)\s+-subject\s+"(.+)"$'
    match3 = re.match(correct_pattern, arg)
    print(f"Correct pattern match: {match3}")
    if match3:
        print(f"Correct pattern groups: {match3.groups()}")