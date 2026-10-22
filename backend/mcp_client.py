import json
import os
import sys

import anyio
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8100/mcp")

# command -> (tool name, needs project id)
COMMANDS = {
    "list": ("list_projects", False),
    "get": ("get_project", True),
    "requirements": ("get_project_requirements", True),
    "prd": ("get_project_prd", True),
    "tasks": ("get_project_tasks", True),
    "sprint": ("get_sprint_plan", True),
    "brief": ("get_build_brief", True),
    "generate": ("generate_project_spec", True),
}

USAGE = (
    "Usage:\n"
    "  python mcp_client.py tools\n"
    "  python mcp_client.py list\n"
    "  python mcp_client.py <get|requirements|prd|tasks|sprint|brief|generate> <project_id>\n"
    "\n"
    "Save Markdown to a UTF-8 file (recommended on Windows):\n"
    "  python mcp_client.py brief 21 --out brief_21.md"
)


async def run(tool: str | None, args: dict, out_path: str | None = None):
    api_key = os.getenv("MCP_API_KEY")
    if not api_key:
        raise SystemExit("Set the MCP_API_KEY environment variable first.")

    http_client = httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=330,
    )

    async with http_client:
        transport = streamable_http_client(MCP_URL, http_client=http_client)
        async with Client(transport, read_timeout_seconds=330) as client:
            if tool is None:
                result = await client.list_tools()
                print("Available tools:")
                for t in result.tools:
                    print("-", t.name)
                return

            response = await client.call_tool(tool, args)
            text = response.content[0].text

            if response.is_error:
                print("Tool error:", text)
                return

            # Markdown tools: print or save the document itself.
            try:
                data = json.loads(text)
            except ValueError:
                print(text)
                return

            if isinstance(data, dict) and data.get("success") and "markdown" in data:
                if data.get("missing_sections"):
                    print(
                        "<!-- missing sections: "
                        + ", ".join(data["missing_sections"])
                        + " -->",
                        file=sys.stderr,
                    )
                if out_path:
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(data["markdown"])
                    print(f"Saved to {out_path}")
                else:
                    print(data["markdown"])
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))


def _root_error(exc: BaseException) -> BaseException:
    while getattr(exc, "exceptions", None):
        exc = exc.exceptions[0]
    return exc


def go(tool, args, out_path=None):
    try:
        anyio.run(run, tool, args, out_path)
    except SystemExit:
        raise
    except BaseException as exc:
        root = _root_error(exc)
        raise SystemExit(
            f"Request failed: {type(root).__name__}: {root}\n"
            "If this is a connection or 401 error: check that the MCP server is "
            "running, MCP_API_KEY matches the server's key, and MCP_URL is correct."
        )


if __name__ == "__main__":
    # Windows consoles default to cp1252, which cannot print characters such
    # as the non-breaking hyphen (U+2011) that LLMs often produce.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    argv = sys.argv[1:]
    out_path = None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            raise SystemExit("--out needs a file name, e.g. --out brief_21.md")
        out_path = argv[i + 1]
        del argv[i:i + 2]

    if len(argv) < 1:
        raise SystemExit(USAGE)

    command = argv[0]

    if command == "tools" and len(argv) == 1:
        go(None, {})
    elif command in COMMANDS:
        tool_name, needs_id = COMMANDS[command]
        if needs_id:
            if len(argv) != 2:
                raise SystemExit(USAGE)
            project_id = int(argv[1])
            if project_id <= 0:
                raise SystemExit("Project ID must be positive.")
            go(tool_name, {"project_id": project_id}, out_path)
        else:
            if len(argv) != 1:
                raise SystemExit(USAGE)
            go(tool_name, {}, out_path)
    else:
        raise SystemExit(USAGE)