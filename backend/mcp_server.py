import os

import httpx
from mcp.server import MCPServer

mcp = MCPServer("SpecPilot MCP Server")

SPEC_PILOT_API = os.getenv("SPECPILOT_API", "http://127.0.0.1:8000")


@mcp.tool()
async def generate_project_spec(project_id: int) -> dict:
    """Run the existing SpecPilot project-generation pipeline."""

    if project_id <= 0:
        return {
            "success": False,
            "error": "project_id must be positive",
        }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{SPEC_PILOT_API}/generation/run/{project_id}"
            )
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "project_id": project_id,
                "status": data.get("status"),
                "tasks_created": data.get("tasks_created"),
                "has_prd": bool(data.get("prd")),
                "has_sprint_plan": bool(data.get("sprint_plan")),
            }

    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "project_id": project_id,
            "error": "SpecPilot API returned an error",
            "status_code": exc.response.status_code,
            "details": exc.response.text[:2000],
        }

    except httpx.RequestError as exc:
        return {
            "success": False,
            "project_id": project_id,
            "error": "Could not connect to SpecPilot backend",
            "details": str(exc),
        }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8100,
    )