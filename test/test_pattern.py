import re

# Test the exact pattern from the file
arg = '2 -subject "Updated Child Subject"'
print(f"Testing with arg: {arg!r}")

subject_match = re.match(r'^(\\d+)\\s+-subject\\s+\"(.+)\"$', arg, re.DOTALL)
parent_match = re.match(r'^(\\d+)\\s+-parent\\s+(\\d+|None|none|null|NULL)$', arg.strip())

print(f"Subject match: {subject_match}")
if subject_match:
    print(f"Groups: {subject_match.groups()}")

print(f"Parent match: {parent_match}")
if parent_match:
    print(f"Groups: {parent_match.groups()}")

# Let's also test the parent pattern
arg2 = '2 -parent None'
parent_match2 = re.match(r'^(\\d+)\\s+-parent\\s+(\\d+|None|none|null|NULL)$', arg2.strip())
print(f"\nTesting parent pattern with: {arg2!r}")
print(f"Parent match: {parent_match2}")
if parent_match2:
    print(f"Groups: {parent_match2.groups()}")