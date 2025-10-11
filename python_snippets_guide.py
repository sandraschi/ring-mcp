#!/usr/bin/env python3
"""
🚀 Python Snippets Usage Guide
Complete examples of how to use the Python snippets from the documentation
"""

# =============================================================================
# 1. BASIC FASTMCP SERVER SETUP
# =============================================================================

print("=== Basic FastMCP Server Setup ===")

from fastmcp import FastMCP

# Create your MCP server
app = FastMCP("my-server")

# Add a simple tool
@app.tool()
def hello_world() -> str:
    """A simple hello world tool."""
    return "Hello from my MCP server!"

# Run the server
if __name__ == "__main__":
    print("Starting MCP server...")
    app.run()

# =============================================================================
# 2. TOOL WITH PARAMETERS AND VALIDATION
# =============================================================================

print("\n=== Tool with Parameters ===")

from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Annotated

class ToolParams(BaseModel):
    name: Annotated[str, {"description": "Name to greet"}]
    age: Annotated[int, {"description": "Age of person"}] = None

app = FastMCP("my-server")

@app.tool()
def greet_person(params: ToolParams) -> str:
    """Greet a person with optional age."""
    if params.age:
        return f"Hello {params.name}! You are {params.age} years old."
    else:
        return f"Hello {params.name}!"

# =============================================================================
# 3. ASYNC TOOL EXAMPLE
# =============================================================================

print("\n=== Async Tool Example ===")

import asyncio
from fastmcp import FastMCP

app = FastMCP("my-server")

@app.tool()
async def async_operation(task_name: str) -> str:
    """An async tool that simulates I/O operations."""
    print(f"Starting async task: {task_name}")
    await asyncio.sleep(1)  # Simulate async work
    print(f"Completed async task: {task_name}")
    return f"Async task '{task_name}' completed successfully!"

# =============================================================================
# 4. ERROR HANDLING EXAMPLE
# =============================================================================

print("\n=== Error Handling Example ===")

import logging
from fastmcp import FastMCP

app = FastMCP("my-server")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.tool()
def safe_operation(input_value: str) -> str:
    """A tool with comprehensive error handling."""
    try:
        logger.info(f"Processing input: {input_value}")

        # Your actual logic here
        if not input_value:
            raise ValueError("Input cannot be empty")

        result = f"Processed: {input_value.upper()}"
        logger.info(f"Operation successful: {result}")

        return result

    except Exception as e:
        logger.error(f"Error in safe_operation: {e}")
        return f"Error processing request: {str(e)}"

# =============================================================================
# 5. MULTIPLE TOOLS IN ONE SERVER
# =============================================================================

print("\n=== Multiple Tools Server ===")

from fastmcp import FastMCP
from datetime import datetime

app = FastMCP("multi-tool-server")

@app.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()

@app.tool()
def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@app.tool()
def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]

# =============================================================================
# 6. PYDANTIC V2 MODEL EXAMPLE
# =============================================================================

print("\n=== Pydantic V2 Model Example ===")

from fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserProfile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    email: str
    age: Optional[int] = None
    preferences: dict = {}

app = FastMCP("user-server")

@app.tool()
def create_user(profile: UserProfile) -> dict:
    """Create a user profile."""
    return {
        "message": f"User {profile.name} created successfully",
        "profile": profile.model_dump()
    }

# =============================================================================
# 7. COMPLETE WORKING EXAMPLE
# =============================================================================

print("\n=== Complete Working Example ===")

from fastmcp import FastMCP
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create server
app = FastMCP("complete-example")

# Simple tools
@app.tool()
def health_check() -> dict:
    """Check server health."""
    return {"status": "healthy", "timestamp": "2025-01-20"}

@app.tool()
def echo_message(message: str) -> str:
    """Echo back the input message."""
    logger.info(f"Echoing message: {message}")
    return f"You said: {message}"

# Complex tool with validation
class MathOperation(BaseModel):
    operation: str  # "add", "subtract", "multiply", "divide"
    a: float
    b: float

@app.tool()
def calculate(operation: MathOperation) -> float:
    """Perform mathematical calculations."""
    try:
        if operation.operation == "add":
            result = operation.a + operation.b
        elif operation.operation == "subtract":
            result = operation.a - operation.b
        elif operation.operation == "multiply":
            result = operation.a * operation.b
        elif operation.operation == "divide":
            if operation.b == 0:
                raise ValueError("Cannot divide by zero")
            result = operation.a / operation.b
        else:
            raise ValueError(f"Unknown operation: {operation.operation}")

        logger.info(f"Calculation: {operation.a} {operation.operation} {operation.b} = {result}")
        return result

    except Exception as e:
        logger.error(f"Calculation error: {e}")
        raise

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting MCP Server with examples...")
    print("Available tools:")
    print("- health_check() -> dict")
    print("- echo_message(message: str) -> str")
    print("- calculate(operation: MathOperation) -> float")
    print()
    print("Run with: python python_snippets_guide.py")
    print("Or import and use individual examples")

    # Uncomment to run server
    # app.run()

# =============================================================================
# HOW TO USE THESE SNIPPETS
# =============================================================================

"""
QUICK START GUIDE:

1. CREATE A NEW FILE:
   touch my_mcp_server.py

2. COPY A SNIPPET:
   - Copy the Basic FastMCP Server Setup
   - Or any other example that fits your needs

3. INSTALL DEPENDENCIES:
   pip install fastmcp pydantic

4. RUN THE SERVER:
   python my_mcp_server.py

5. TEST IN ANOTHER TERMINAL:
   # List available tools
   curl -X POST http://localhost:8000/tools \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

   # Call a tool
   curl -X POST http://localhost:8000/tools \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "hello_world"}}'

ALTERNATIVE: Use MCPJam for testing
   npx mcpjam test --server "python my_mcp_server.py"
"""



