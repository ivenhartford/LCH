#!/usr/bin/env python3
"""
Fix all pytest fixtures that use app.app_context() but don't have 'app' parameter.
"""

import re
import glob
import sys

def fix_fixture_app_param(filepath):
    """Add 'app' parameter to fixtures that use app.app_context() but don't have it."""
    with open(filepath, 'r') as f:
        content = f.read()

    original = content
    lines = content.split('\n')
    modified = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a fixture decorator
        if '@pytest.fixture' in line:
            # Get the decorator line(s)
            decorator_start = i
            i += 1

            # Skip any additional decorator parameters on next lines
            while i < len(lines) and not lines[i].strip().startswith('def '):
                i += 1

            if i >= len(lines):
                break

            # Get the function definition line
            func_line = lines[i]

            # Extract function name and parameters
            match = re.match(r'(\s*)def\s+(\w+)\((.*?)\):', func_line)
            if not match:
                i += 1
                continue

            indent = match.group(1)
            func_name = match.group(2)
            params = match.group(3).strip()

            # Skip if this is the 'app' fixture itself
            if func_name == 'app':
                i += 1
                continue

            # Check if 'app' is already in parameters
            param_list = [p.strip().split('=')[0].strip() for p in params.split(',') if p.strip()]
            if 'app' in param_list:
                i += 1
                continue

            # Look ahead in the function body to see if it uses app.app_context()
            # Scan the next 50 lines or until we hit another function
            uses_app_context = False
            j = i + 1
            indent_level = len(indent)

            while j < len(lines) and j < i + 100:
                check_line = lines[j]

                # Stop if we hit another function at the same or higher level
                if check_line.strip().startswith('def ') and len(check_line) - len(check_line.lstrip()) <= indent_level:
                    break

                # Stop if we hit a class at the same or higher level
                if check_line.strip().startswith('class ') and len(check_line) - len(check_line.lstrip()) <= indent_level:
                    break

                # Check for app.app_context()
                if 'app.app_context()' in check_line:
                    uses_app_context = True
                    break

                j += 1

            # If the fixture uses app.app_context(), add 'app' parameter
            if uses_app_context:
                if params:
                    new_params = f'app, {params}'
                else:
                    new_params = 'app'

                new_func_line = f'{indent}def {func_name}({new_params}):'
                lines[i] = new_func_line
                modified = True
                print(f"  Fixed fixture '{func_name}' in {filepath}")

        i += 1

    if modified:
        new_content = '\n'.join(lines)
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True

    return False

def main():
    test_files = glob.glob('/home/user/LCH/backend/tests/test_*.py')

    fixed_count = 0
    for filepath in sorted(test_files):
        print(f"Checking {filepath}...")
        if fix_fixture_app_param(filepath):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} file(s)")
    return 0

if __name__ == '__main__':
    sys.exit(main())
