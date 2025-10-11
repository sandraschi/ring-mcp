#!/usr/bin/env python3
"""
🚀 Simple MCP Server Example
Copy this to create your own MCP server
"""

from fastmcp import FastMCP

# Create your server
app = FastMCP("simple-example")

@app.tool()
def hello_world() -> str:
    """A simple hello world tool."""
    return "Hello from my first MCP server!"

@app.tool()
def greet_person(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}! Welcome to MCP servers!"

if __name__ == "__main__":
    print("Starting Simple MCP Server...")
    print("Available tools: hello_world, greet_person")
    app.run()



