#!/usr/bin/env python3
"""
Fix syntax error in token_manager.py
"""

def fix_token_manager():
    with open('ring_mcp/core/token_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the clear_tokens method docstring
    old_text = '''        """
        self._tokens = {}
        return await self.save_tokens()'''

    new_text = '''        """
        self._tokens = {}
        return await self.save_tokens()'''

    fixed_content = content.replace(old_text, new_text)

    with open('ring_mcp/core/token_manager.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print("Fixed token_manager.py syntax error")

if __name__ == "__main__":
    fix_token_manager()
