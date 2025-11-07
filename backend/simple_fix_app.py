#!/usr/bin/env python3
"""
Simple script to add 'app' parameter to functions that use app.app_context() but don't have it.
"""

import glob
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content
    lines = content.split('\n')
    modified_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line contains a function definition (fixture or test method)
        if ('def test_' in line and 'self' in line) or \
           (i > 0 and '@pytest.fixture' in lines[i-1] and 'def ' in line):

            # Extract function name
            func_match = re.search(r'def\s+(\w+)\s*\(', line)
            if not func_match:
                modified_lines.append(line)
                i += 1
                continue

            func_name = func_match.group(1)

            # Skip if this is the app fixture
            if func_name == 'app':
                modified_lines.append(line)
                i += 1
                continue

            # Check if 'app' is already in the parameters
            if re.search(r'\(\s*app\s*[,)]', line) or ', app,' in line or '(app)' in line:
                modified_lines.append(line)
                i += 1
                continue

            # Look ahead to see if function uses app.app_context()
            uses_app_context = False
            for j in range(i+1, min(i+100, len(lines))):
                if 'app.app_context()' in lines[j]:
                    uses_app_context = True
                    break
                # Stop at next function
                if lines[j].strip().startswith('def '):
                    break

            if uses_app_context:
                # Add app parameter
                if 'self,' in line:
                    # It's a test method with self
                    new_line = line.replace('self,', 'self, app,', 1)
                elif 'self)' in line:
                    # self is the only parameter
                    new_line = line.replace('self)', 'self, app)', 1)
                elif '(' in line and ')' in line:
                    # Regular function/fixture
                    # Find the opening paren
                    paren_idx = line.index('(')
                    close_paren_idx = line.index(')')
                    params = line[paren_idx+1:close_paren_idx].strip()
                    if params:
                        new_params = f'app, {params}'
                    else:
                        new_params = 'app'
                    new_line = line[:paren_idx+1] + new_params + line[close_paren_idx:]
                else:
                    # Multiline signature - skip for now
                    modified_lines.append(line)
                    i += 1
                    continue

                modified_lines.append(new_line)
                print(f"  Fixed {func_name} in {filepath}")
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

        i += 1

    new_content = '\n'.join(modified_lines)

    if new_content != original_content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True

    return False

def main():
    test_files = glob.glob('/home/user/LCH/backend/tests/test_*.py')

    fixed_count = 0
    fixed_functions = 0

    for filepath in sorted(test_files):
        print(f"Processing {filepath}...")
        result = fix_file(filepath)
        if result:
            fixed_count += 1

    print(f"\n✅ Fixed functions in {fixed_count} files")

if __name__ == '__main__':
    main()
