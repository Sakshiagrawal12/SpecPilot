from mcp.server import MCPServer


mcp = MCPServer("SpecPilot MCP Server")


@mcp.tool()
def hello(name: str) -> str:
    """Return a greeting from the SpecPilot MCP server."""
    return f"Hello {name}, SpecPilot MCP server is working!"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8100,
    )