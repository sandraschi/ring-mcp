#!/usr/bin/env python3
"""
Fix the syntax error in token_manager.py
"""

import re

def fix_token_manager():
    with open('ring_mcp/core/token_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Find the problematic area around line 315
    for i in range(310, 320):
        if i < len(lines):
            line = lines[i]
            print(f'Line {i+1}: {repr(line)}')

    # Fix the docstring issue
    # The docstring starts at line 311 with """ but never closes properly
    if '"""Clear all stored tokens.' in content:
        # Find the position of the docstring
        start_pos = content.find('"""Clear all stored tokens.')
        end_pos = content.find('"""\n        self._tokens = {}')

        if start_pos != -1 and end_pos != -1:
            # Replace the problematic section
            before = content[:start_pos]
            after = content[end_pos:]

            # Fix the docstring
            fixed_section = '''    async def clear_tokens(self) -> bool:
        """Clear all stored tokens.

        Returns:
            bool: True if the tokens were cleared successfully, False otherwise
        """
        self._tokens = {}
        return await self.save_tokens()'''

            fixed_content = before + fixed_section + after
            print("Fixed content preview:")
            print(repr(fixed_content[start_pos:start_pos+200]))

            # Write the fixed content
            with open('ring_mcp/core/token_manager.py', 'w', encoding='utf-8') as f:
                f.write(fixed_content)

            print("Fixed token_manager.py syntax error")

if __name__ == "__main__":
    fix_token_manager()
