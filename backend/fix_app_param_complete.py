#!/usr/bin/env python3
"""Comprehensive fix to add 'app' parameter to all fixtures using app.app_context()."""

import re
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Pattern to match fixture definitions
    # @pytest.fixture\ndef function_name(params):
    pattern = r'(@pytest\.fixture[^\n]*\n)(def\s+(\w+)\(([^)]*)\):)'

    def fix_fixture(match):
        decorator = match.group(1)
        full_def = match.group(2)
        func_name = match.group(3)
        params = match.group(4).strip()

        # Skip if app is already in params or if this is the app fixture itself
        if func_name == 'app' or 'app' in [p.strip().split('=')[0] for p in params.split(',') if p.strip()]:
            return match.group(0)

        # Find the function body to check if it uses app.app_context()
        # Look for the function in the content
        func_start = match.end()
        # Find next function or end of file
        next_func = content.find('\ndef ', func_start)
        next_decorator = content.find('\n@', func_start)

        func_end = len(content)
        if next_func > 0:
            func_end = min(func_end, next_func)
        if next_decorator > 0:
            func_end = min(func_end, next_decorator)

        func_body = content[func_start:func_end]

        # Check if function uses app.app_context()
        if 'app.app_context()' in func_body:
            # Add app as first parameter
            if params:
                new_params = f'app, {params}'
            else:
                new_params = 'app'
            new_def = full_def.replace(f'({params})', f'({new_params})')
            return decorator + new_def

        return match.group(0)

    content = re.sub(pattern, fix_fixture, content)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Fix all test files
test_files = glob.glob('/home/user/LCH/backend/tests/test_*.py')
fixed = 0

for filepath in test_files:
    if fix_file(filepath):
        fixed += 1
        print(f"Fixed: {filepath}")

print(f"\n✅ Fixed {fixed} files")
