import sys
import anyio
from mcp import Client


async def main(project_id: int):
    async with Client(
        "http://127.0.0.1:8100/mcp",
        read_timeout_seconds=330,
    ) as client:
        result = await client.list_tools()

        print("Available tools:")
        for tool in result.tools:
            print("-", tool.name)

        response = await client.call_tool(
            "generate_project_spec",
            {"project_id": project_id},
        )

        if response.is_error:
            print("Tool error:", response.content[0].text)
        else:
            print(response.content[0].text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mcp_client.py <project_id>")
        raise SystemExit(1)

    project_id = int(sys.argv[1])

    if project_id <= 0:
        raise SystemExit("Project ID must be positive.")

    anyio.run(main, project_id)