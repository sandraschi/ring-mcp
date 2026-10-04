"""
Ring MCP Help System Tools - FastMCP 3.4.

Tool discovery and listing, detailed per-tool help, and search over the
served tool catalog (kept in sync with the registered surface).
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)

_READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}


def register_tools(app: FastMCP) -> None:
    """Register help system tools with the FastMCP application.

    Args: See Parameters block.
    """

    @app.tool(
        name="list_available_tools",
        description="List all available Ring MCP tools with categories and descriptions",
        annotations=_READ_ONLY,
    )
    async def list_available_tools(
        category: Annotated[
            str | None,
            Field(
                description="Filter by category (cameras, doorbells, security, fire, monitoring, automation, system, help)."
            ),
        ] = None,
        include_hidden: Annotated[bool, Field(description="Include internal tools.")] = False,
    ) -> dict[str, Any]:
        """List all available Ring MCP tools with categories and descriptions.

        ## Return Format
        {"success": true, "tools": [...], "categories": [...], "total_count": N, ...}

        ## Examples
        await list_available_tools()
        await list_available_tools(category="cameras")
        """
        # Tool registry - comprehensive list of all Ring MCP tools
        all_tools = {
            # Camera Management Tools
            "cameras": [
                {
                    "name": "get_camera_status",
                    "description": "Get comprehensive status of all Ring security cameras",
                    "category": "cameras",
                    "parameters": {},
                    "example": "get_camera_status()",
                    "returns": "Camera status including online/offline, battery, recording",
                },
                {
                    "name": "stream_all_cameras",
                    "description": "Start live video streams from all cameras",
                    "category": "cameras",
                    "parameters": {},
                    "example": "stream_all_cameras()",
                    "returns": "Live stream URLs and status for all cameras",
                },
            ],
            # Doorbell Management Tools
            "doorbells": [
                {
                    "name": "get_doorbell_status",
                    "description": "Get comprehensive status of all Ring doorbells",
                    "category": "doorbells",
                    "parameters": {},
                    "example": "get_doorbell_status()",
                    "returns": "Doorbell connectivity, battery, and visitor detection status",
                },
                {
                    "name": "get_doorbell_live_stream",
                    "description": "WebRTC live-view handoff for a doorbell (direct URLs are retired)",
                    "category": "doorbells",
                    "parameters": {"doorbell_id": "string", "quality": "low|medium|high", "duration_seconds": "int"},
                    "example": "get_doorbell_live_stream(doorbell_id='doorbell-001')",
                    "returns": "WebRTC signaling endpoints for the doorbell",
                },
                {
                    "name": "answer_doorbell_call",
                    "description": "Two-way audio status (not implemented in this backend)",
                    "category": "doorbells",
                    "parameters": {"doorbell_id": "string"},
                    "example": "answer_doorbell_call(doorbell_id='doorbell-001')",
                    "returns": "Explicit unsupported error",
                },
                {
                    "name": "get_visitor_history",
                    "description": "Get visitor history and activity logs",
                    "category": "doorbells",
                    "parameters": {"hours": "int", "include_snapshots": "bool", "motion_only": "bool"},
                    "example": "get_visitor_history(hours=24, motion_only=True)",
                    "returns": "Recent visitor activity and motion events",
                },
                {
                    "name": "configure_motion_detection",
                    "description": "Motion configuration status (not exposed by the Ring API wrapper)",
                    "category": "doorbells",
                    "parameters": {"doorbell_id": "string", "sensitivity": "low|medium|high"},
                    "example": "configure_motion_detection(sensitivity='low')",
                    "returns": "Explicit unsupported error with requested config echo",
                },
            ],
            # Security System Tools
            "security": [
                {
                    "name": "get_security_system_status",
                    "description": "Get comprehensive status of the entire Ring security system",
                    "category": "security",
                    "parameters": {},
                    "example": "get_security_system_status()",
                    "returns": "Overall security system status, modes, and device health",
                },
                {
                    "name": "arm_security_system",
                    "description": "Arm the alarm panel in home/away mode (or disarm)",
                    "category": "security",
                    "parameters": {"mode": "home|away|disarmed", "device_id": "string"},
                    "example": "arm_security_system(mode='away')",
                    "returns": "Arming status for the panel",
                },
                {
                    "name": "disarm_security_system",
                    "description": "Disarm the alarm panel",
                    "category": "security",
                    "parameters": {"force_disarm": "bool", "device_id": "string"},
                    "example": "disarm_security_system()",
                    "returns": "Disarming status and system state",
                },
                {
                    "name": "get_security_history",
                    "description": "Get security system history and events",
                    "category": "security",
                    "parameters": {"hours": "int", "event_types": "list", "include_video": "bool"},
                    "example": "get_security_history(hours=24)",
                    "returns": "Security events and system activity logs",
                },
            ],
            # Fire Safety Tools
            "fire": [
                {
                    "name": "get_fire_alarm_status",
                    "description": "Get comprehensive status of all Ring fire alarms and smoke detectors",
                    "category": "fire",
                    "parameters": {},
                    "example": "get_fire_alarm_status()",
                    "returns": "Fire alarm health, battery levels, and system status",
                },
                {
                    "name": "test_fire_safety_system",
                    "description": "Test fire safety system components",
                    "category": "fire",
                    "parameters": {},
                    "example": "test_fire_safety_system()",
                    "returns": "Test results and system health report",
                },
            ],
            # Monitoring Tools
            "monitoring": [
                {
                    "name": "monitor_system_health",
                    "description": "Perform comprehensive health check of entire Ring security system",
                    "category": "monitoring",
                    "parameters": {},
                    "example": "monitor_system_health()",
                    "returns": "System health score, device status, and maintenance alerts",
                },
                {
                    "name": "get_real_time_activity",
                    "description": "Get real-time activity and alerts from all devices",
                    "category": "monitoring",
                    "parameters": {},
                    "example": "get_real_time_activity()",
                    "returns": "Recent activity, motion events, and system alerts",
                },
            ],
            # Automation Tools
            "automation": [
                {
                    "name": "create_security_automation",
                    "description": "Create custom security automation rule with triggers and responses",
                    "category": "automation",
                    "parameters": {
                        "trigger_type": "string",
                        "trigger_conditions": "dict",
                        "response_actions": "list",
                        "automation_name": "string",
                    },
                    "example": "create_security_automation(trigger_type='motion', automation_name='Front Door Alert')",
                    "returns": "Automation rule creation status and ID",
                },
                {
                    "name": "trigger_emergency_protocol",
                    "description": "Trigger emergency response protocol",
                    "category": "automation",
                    "parameters": {},
                    "example": "trigger_emergency_protocol()",
                    "returns": "Emergency protocol activation status",
                },
                {
                    "name": "schedule_security_modes",
                    "description": "Schedule automatic security mode changes",
                    "category": "automation",
                    "parameters": {"schedule_config": "dict", "timezone": "string"},
                    "example": "schedule_security_modes(schedule_config={'modes': ['armed'], 'timeframes': []})",
                    "returns": "Schedule creation status and validation",
                },
            ],
            # System Tools
            "system": [
                {
                    "name": "get_system_status",
                    "description": "Get detailed system status including auth and device connectivity",
                    "category": "system",
                    "parameters": {"include_device_details": "bool", "check_connectivity": "bool"},
                    "example": "get_system_status()",
                    "returns": "Authentication status, device connectivity, and system health",
                },
                {
                    "name": "check_authentication_status",
                    "description": "Check Ring API authentication status and token validity",
                    "category": "system",
                    "parameters": {},
                    "example": "check_authentication_status()",
                    "returns": "Authentication state and errors",
                },
                {
                    "name": "check_device_connectivity",
                    "description": "Test connectivity and status of all Ring devices",
                    "category": "system",
                    "parameters": {"device_id": "string", "test_commands": "bool"},
                    "example": "check_device_connectivity()",
                    "returns": "Per-device connectivity results and score",
                },
                {
                    "name": "get_service_health",
                    "description": "Get detailed service health and performance metrics",
                    "category": "system",
                    "parameters": {"include_metrics": "bool", "history_minutes": "int"},
                    "example": "get_service_health()",
                    "returns": "Component health, score, alerts, recommendations",
                },
                {
                    "name": "list_devices",
                    "description": "List all Ring devices with online status and battery",
                    "category": "system",
                    "parameters": {"device_type": "string"},
                    "example": "list_devices(device_type='camera')",
                    "returns": "Device inventory with count",
                },
                {
                    "name": "show_devices_card",
                    "description": "Show all Ring devices as a rich in-chat card",
                    "category": "system",
                    "parameters": {},
                    "example": "show_devices_card()",
                    "returns": "Prefab card payload",
                },
                {
                    "name": "show_health_card",
                    "description": "Show Ring MCP health as a rich in-chat card",
                    "category": "system",
                    "parameters": {},
                    "example": "show_health_card()",
                    "returns": "Prefab card payload",
                },
                {
                    "name": "ring_shutdown",
                    "description": "Gracefully shut down the Ring MCP server",
                    "category": "system",
                    "parameters": {},
                    "example": "ring_shutdown()",
                    "returns": "Shutdown acknowledgement",
                },
            ],
            # Help Tools
            "help": [
                {
                    "name": "list_available_tools",
                    "description": "List all available Ring MCP tools with categories",
                    "category": "help",
                    "parameters": {"category": "string", "include_hidden": "bool"},
                    "example": "list_available_tools(category='cameras')",
                    "returns": "Tool catalog with count",
                },
                {
                    "name": "get_tool_help",
                    "description": "Get detailed help for a specific tool",
                    "category": "help",
                    "parameters": {"tool_name": "string"},
                    "example": "get_tool_help(tool_name='list_devices')",
                    "returns": "Tool detail with examples and related tools",
                },
                {
                    "name": "search_tools",
                    "description": "Search for tools by name, description, or functionality",
                    "category": "help",
                    "parameters": {"query": "string"},
                    "example": "search_tools(query='camera')",
                    "returns": "Ranked tool matches",
                },
            ],
        }

        # Flatten tools list
        tools = []
        categories = set()

        for category_tools in all_tools.values():
            for tool in category_tools:
                tools.append(tool)
                categories.add(tool["category"])

        # Filter by category if specified
        if category:
            tools = [t for t in tools if t["category"] == category]

        # Filter out hidden tools unless requested
        if not include_hidden:
            tools = [t for t in tools if t["category"] != "internal"]

        return {
            "success": True,
            "message": f"{len(tools)} tool(s) listed",
            "tools": tools,
            "categories": sorted(list(categories)),
            "total_count": len(tools),
            "filtered_count": len(tools),
            "timestamp": datetime.now().isoformat(),
        }

    @app.tool(
        name="get_tool_help",
        description="Get detailed help and usage information for a specific tool",
        annotations=_READ_ONLY,
    )
    async def get_tool_help(
        tool_name: Annotated[str, Field(description="Name of the tool to get help for.", min_length=1)],
        include_examples: Annotated[bool, Field(description="Include usage examples.")] = True,
    ) -> dict[str, Any]:
        """Get detailed help and usage information for a specific tool.

        ## Return Format
        {"success": true, "tool_name": "...", "description": "...", "examples": {...}, ...}

        ## Examples
        await get_tool_help(tool_name="list_devices")
        """
        # Get all tools
        all_tools_response = await list_available_tools(include_hidden=True)
        all_tools = all_tools_response["tools"]

        # Find the specific tool
        tool = None
        for t in all_tools:
            if t["name"] == tool_name:
                tool = t
                break

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": [t["name"] for t in all_tools],
                "suggestion": "Use 'list_available_tools()' to see all available tools",
            }

        # Enhanced help information
        help_info = {
            "success": True,
            "message": f"Help for '{tool['name']}'",
            "tool_name": tool["name"],
            "description": tool["description"],
            "category": tool["category"],
            "parameters": tool["parameters"],
            "returns": tool["returns"],
            "usage": tool["example"],
        }

        if include_examples:
            help_info["examples"] = {
                "basic": tool["example"],
                "advanced": generate_advanced_example(tool),
                "error_handling": generate_error_handling_example(tool),
            }

            help_info["tips"] = generate_usage_tips(tool)
            help_info["related_tools"] = find_related_tools(tool, all_tools)

        return help_info

    @app.tool(
        name="search_tools",
        description="Search for tools by name, description, or functionality",
        annotations=_READ_ONLY,
    )
    async def search_tools(
        query: Annotated[str, Field(description="Search query text.", min_length=1)],
        category: Annotated[str | None, Field(description="Optional category filter.")] = None,
        limit: Annotated[int, Field(description="Maximum results.", ge=1, le=50)] = 10,
    ) -> dict[str, Any]:
        """Search for tools by name, description, or functionality.

        ## Return Format
        {"success": true, "query": "...", "total_matches": N, "results": [...]}

        ## Examples
        await search_tools(query="camera")
        """
        # Get all tools
        all_tools_response = await list_available_tools(include_hidden=True)
        all_tools = all_tools_response["tools"]

        # Search algorithm
        matches = []
        query_lower = query.lower()

        for tool in all_tools:
            relevance_score = 0

            # Exact name match - highest priority
            if query_lower == tool["name"].lower():
                relevance_score = 100
            # Partial name match
            elif query_lower in tool["name"].lower():
                relevance_score = 80
            # Description match
            elif query_lower in tool["description"].lower():
                relevance_score = 60
            # Category match
            elif category and tool["category"] == category.lower():
                relevance_score = 40
            # Parameter match
            elif any(query_lower in str(param).lower() for param in tool["parameters"].values()):
                relevance_score = 50
            # Use case match
            elif query_lower in tool["returns"].lower():
                relevance_score = 30

            if relevance_score > 0:
                tool["relevance_score"] = relevance_score
                tool["match_type"] = get_match_type(relevance_score)
                matches.append(tool)

        # Sort by relevance score
        matches.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Limit results
        matches = matches[:limit]

        return {
            "success": True,
            "message": f"{len(matches)} match(es) for '{query}'",
            "query": query,
            "category_filter": category,
            "total_matches": len(matches),
            "results": matches,
            "search_tips": [
                "Use exact tool names for best results",
                "Try partial names or keywords",
                "Specify category for focused results",
                "Check parameter names and descriptions",
            ],
        }


def generate_advanced_example(tool: dict[str, Any]) -> str:
    """Generate advanced usage examples for a tool."""
    examples = {
        "get_camera_status": "get_camera_status()  # Get all cameras with detailed status",
        "get_doorbell_status": "get_doorbell_status()  # Monitor visitor detection and battery",
        "monitor_system_health": "monitor_system_health()  # Comprehensive system check",
        "get_security_system_status": "get_security_system_status()  # Check security mode and devices",
    }
    return examples.get(tool["name"], f"{tool['name']}()  # Advanced usage with error handling")


def generate_error_handling_example(tool: dict[str, Any]) -> str:
    """Generate error handling examples for a tool."""
    return f"""try:
    result = await {tool["name"]}()
    print(f"Success: {{result}}")
except ValueError as e:
    print(f"Authentication/parameter error: {{e}}")
except Exception as e:
    print(f"Unexpected error: {{e}}")
    # Tools are designed to handle errors gracefully"""


def generate_usage_tips(tool: dict[str, Any]) -> list[str]:
    """Generate usage tips for a tool."""
    tips = []

    if "camera" in tool["name"]:
        tips.extend(
            [
                "Check camera status before streaming",
                "Monitor battery levels regularly",
                "Test motion detection in different lighting",
            ]
        )
    elif "doorbell" in tool["name"]:
        tips.extend(
            [
                "Configure motion zones for better detection",
                "Check visitor history regularly",
                "Test call answering functionality",
            ]
        )
    elif "security" in tool["name"]:
        tips.extend(
            [
                "Set up entry/exit delays appropriately",
                "Test alarm system regularly",
                "Monitor device connectivity status",
            ]
        )
    elif "fire" in tool["name"]:
        tips.extend(["Test smoke detectors monthly", "Replace batteries annually", "Clean sensors regularly"])
    else:
        tips.append("Check tool help for detailed usage instructions")

    return tips


def find_related_tools(tool: dict[str, Any], all_tools: list[dict[str, Any]]) -> list[str]:
    """Find tools related to the current tool."""
    related = []
    current_category = tool["category"]

    # Find tools in same category
    for t in all_tools:
        if t["category"] == current_category and t["name"] != tool["name"]:
            related.append(t["name"])

    return related[:5]  # Limit to 5 related tools


def get_match_type(score: int) -> str:
    """Get human-readable match type based on relevance score."""
    if score >= 80:
        return "exact_match"
    elif score >= 60:
        return "partial_match"
    elif score >= 40:
        return "category_match"
    else:
        return "related_match"
