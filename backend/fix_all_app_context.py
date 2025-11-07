#!/usr/bin/env python3
"""
Comprehensively fix all functions that use app.app_context() but don't have 'app' parameter.
Handles fixtures and test methods with multiline definitions.
"""

import re
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    modified = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for fixture decorator or test method definition
        if '@pytest.fixture' in line or (line.strip().startswith('def test_') and 'self' in line):
            # Collect the complete function definition
            func_start = i
            i += 1

            # Skip decorator parameters or find the def line
            while i < len(lines) and not lines[i].strip().startswith('def '):
                i += 1

            if i >= len(lines):
                break

            # Now at the def line - collect the complete signature
            def_line_start = i
            signature_lines = []

            # Collect until we find the closing ): of the function signature
            paren_count = 0
            started = False
            complete = False

            while i < len(lines):
                sig_line = lines[i]
                signature_lines.append((i, sig_line))

                for char in sig_line:
                    if char == '(':
                        paren_count += 1
                        started = True
                    elif char == ')':
                        paren_count -= 1
                        if started and paren_count == 0:
                            complete = True
                            break

                if complete:
                    break

                i += 1

            if not complete:
                i += 1
                continue

            # Extract function info
            full_signature = ''.join([l for _, l in signature_lines])
            match = re.search(r'def\s+(\w+)\s*\((.*?)\)\s*:', full_signature, re.DOTALL)

            if not match:
                i += 1
                continue

            func_name = match.group(1)
            params = match.group(2)

            # Skip if this is the app fixture itself
            if func_name == 'app':
                i += 1
                continue

            # Check if app already in params
            param_list = [p.strip().split('=')[0].split(':')[0].strip()
                          for p in params.split(',') if p.strip()]
            if 'app' in param_list:
                i += 1
                continue

            # Now check if the function body uses app.app_context()
            # Scan ahead to check function body
            uses_app_context = False
            j = i + 1
            indent_level = len(lines[def_line_start]) - len(lines[def_line_start].lstrip())

            for check_idx in range(j, min(j + 100, len(lines))):
                check_line = lines[check_idx]

                # Stop at next function/class at same or higher level
                stripped = check_line.strip()
                if (stripped.startswith('def ') or stripped.startswith('class ')) and \
                   len(check_line) - len(check_line.lstrip()) <= indent_level:
                    break

                if 'app.app_context()' in check_line:
                    uses_app_context = True
                    break

            if not uses_app_context:
                i += 1
                continue

            # Add 'app' parameter - need to modify the first def line
            first_def_idx, first_def_line = signature_lines[0]

            # Handle multiline signatures
            if len(signature_lines) == 1:
                # Single line signature
                new_line = re.sub(
                    r'(def\s+' + re.escape(func_name) + r'\s*\()(',
                    r'\1app, ',
                    first_def_line
                )
                if params.strip():
                    lines[first_def_idx] = new_line
                else:
                    new_line = re.sub(
                        r'(def\s+' + re.escape(func_name) + r'\s*\()\s*\)',
                        r'\1app)',
                        first_def_line
                    )
                    lines[first_def_idx] = new_line
            else:
                # Multiline signature - add app on the second line
                new_line = first_def_line.rstrip() + '\n'
                lines[first_def_idx] = new_line

                second_idx, second_line = signature_lines[1]
                indent = len(second_line) - len(second_line.lstrip())
                indent_str = ' ' * indent
                lines[second_idx] = f'{indent_str}app, {second_line.lstrip()}'

            modified = True
            print(f"  Fixed {func_name} in {filepath}")

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
