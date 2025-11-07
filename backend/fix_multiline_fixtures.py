#!/usr/bin/env python3
"""
Fix all pytest fixtures that use app.app_context() but don't have 'app' parameter.
Handles multiline function definitions.
"""

import re
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Find all fixtures with their complete definitions
    # Pattern: @pytest.fixture ... def func_name(...): ... app.app_context()

    # Use regex with DOTALL to handle multiline
    pattern = r'(@pytest\.fixture[^\n]*\n(?:[^\n]*\n)*?)(def\s+(\w+)\s*\(((?:[^)]|\n)*?)\)\s*:)'

    def check_and_fix(match):
        decorator = match.group(1)
        func_def = match.group(2)
        func_name = match.group(3)
        params = match.group(4)

        # Skip if this is the app fixture itself
        if func_name == 'app':
            return match.group(0)

        # Check if 'app' already in params
        param_list = [p.strip().split('=')[0].split(':')[0].strip()
                      for p in params.split(',') if p.strip()]
        if 'app' in param_list:
            return match.group(0)

        # Get the rest of the text after this match to check function body
        rest_start = match.end()
        rest_text = content[rest_start:rest_start+2000]  # Check next 2000 chars

        # Find the function body (until next def or class at same level)
        lines_after = rest_text.split('\n')
        func_body_lines = []
        for line in lines_after[:50]:  # Check first 50 lines
            if line.strip().startswith('def ') or line.strip().startswith('class '):
                break
            func_body_lines.append(line)

        func_body = '\n'.join(func_body_lines)

        # Check if function uses app.app_context()
        if 'app.app_context()' not in func_body:
            return match.group(0)

        # Add 'app' parameter
        params_stripped = params.strip()
        if params_stripped:
            # Preserve formatting
            if '\n' in params:
                # Multiline params - add app at the start
                new_params = 'app, ' + params_stripped
            else:
                new_params = 'app, ' + params_stripped
        else:
            new_params = 'app'

        new_func_def = f'def {func_name}({new_params}):'
        result = decorator + new_func_def

        print(f"  Fixed {func_name} in {filepath}")
        return result

    new_content = re.sub(pattern, check_and_fix, content, flags=re.MULTILINE)

    if new_content != original:
        with open(filepath, 'w') as f:
            f.write(new_content)
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
