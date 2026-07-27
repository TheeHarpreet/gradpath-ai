"""Permission-controlled MCP adapter for GradPath AI."""

from mcp.server.fastmcp import FastMCP


def create_server() -> FastMCP:
    """Create an MCP server without exposing premature domain tools."""

    return FastMCP(
        "GradPath AI",
        instructions=(
            "Application-tracker tools will be introduced in Step 6 after "
            "authentication, ownership and approval policies exist."
        ),
    )


def main() -> None:
    """Run the local stdio transport."""

    create_server().run(transport="stdio")
