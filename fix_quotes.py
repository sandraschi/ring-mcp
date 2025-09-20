#!/usr/bin/env python3
"""
Fix triple quote conflicts in token_manager.py
"""

with open('ring_mcp/core/token_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace triple quotes with single quotes to avoid conflicts
# Find the clear_tokens method and fix its docstring
start_marker = 'async def clear_tokens(self) -> bool:'
end_marker = 'return await self.save_tokens()'

start_idx = content.find(start_marker)
if start_idx != -1:
    end_idx = content.find(end_marker, start_idx)
    if end_idx != -1:
        method_content = content[start_idx:end_idx + len(end_marker)]

        # Replace triple quotes with single quotes in docstring
        method_content = method_content.replace('"""', "'''")
        method_content = method_content.replace('"""', "'''")

        # Update the content
        content = content[:start_idx] + method_content + content[end_idx + len(end_marker):]

        with open('ring_mcp/core/token_manager.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print('Fixed triple quote conflicts in token_manager.py')
    else:
        print('Could not find end marker')
else:
    print('Could not find start marker')
