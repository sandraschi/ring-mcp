#!/usr/bin/env python3
"""
Simple fix for token_manager.py
"""

with open('temp_token_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the docstring issue
content = content.replace('"""        self._tokens = {}', '"""        self._tokens = {}')

with open('ring_mcp/core/token_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed docstring issue")
