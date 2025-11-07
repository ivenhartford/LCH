#!/usr/bin/env python3
"""Fix remaining test methods that use app.app_context() but don't have 'app' parameter."""

import glob
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    modified = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line contains a test method definition
        if re.search(r'def\s+test_\w+\s*\(.*self.*\)', line):
            # Check if 'app' is already in parameters
            if ', app' in line or '(app,' in line or '(self, app)' in line:
                i += 1
                continue

            # Look ahead to see if this test method uses app.app_context()
            uses_app_context = False
            for j in range(i+1, min(i+50, len(lines))):
                if 'app.app_context()' in lines[j]:
                    uses_app_context = True
                    break
                # Stop at next function
                if re.search(r'^\s{0,8}def\s+', lines[j]):
                    break

            if uses_app_context:
                # Add app parameter after self
                new_line = re.sub(r'\(self,', '(self, app,', line)
                if new_line == line:  # If pattern not found, try self)
                    new_line = re.sub(r'\(self\)', '(self, app)', line)

                if new_line != line:
                    lines[i] = new_line
                    modified = True
                    # Extract function name for logging
                    match = re.search(r'def\s+(\w+)', line)
                    if match:
                        print(f"  Fixed {match.group(1)} in {filepath}")

        i += 1

    if modified:
        with open(filepath, 'w') as f:
            f.writelines(lines)
        return True

    return False

def main():
    test_files = glob.glob('/home/user/LCH/backend/tests/test_*.py')

    fixed_count = 0
    for filepath in sorted(test_files):
        print(f"Processing {filepath}...")
        if fix_file(filepath):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
