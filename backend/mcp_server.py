import json
import logging
import os
from contextvars import ContextVar
from typing import Optional
from urllib.parse import urlsplit

import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

mcp = MCPServer("SpecPilot MCP Server")

logger = logging.getLogger("specpilot.mcp")

SPEC_PILOT_API = os.getenv("SPECPILOT_API", "http://127.0.0.1:8000")

# Filled in for every request by OAuthMiddleware (bottom of this file).
# Each request therefore acts as exactly one signed-in SpecPilot user.
_current_user: ContextVar[Optional[dict]] = ContextVar("current_user", default=None)
_api_token: ContextVar[Optional[str]] = ContextVar("api_token", default=None)


# ============================================================
# AUTH HELPERS (the signed-in user's own short-lived API token)
# ============================================================

class AuthConfigError(Exception):
    pass


class AuthLoginError(Exception):
    pass


async def authenticated_request(method: str, path: str, **kwargs) -> httpx.Response:
    """Send a request to the SpecPilot backend as the signed-in user of this request."""
    token = _api_token.get()
    if not token:
        raise AuthLoginError("Not signed in to SpecPilot")

    timeout = kwargs.pop("timeout", 60.0)
    headers = dict(kwargs.pop("headers", {}))
    headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.request(
            method,
            f"{SPEC_PILOT_API}{path}",
            headers=headers,
            **kwargs,
        )


def _error_for_status(response: httpx.Response, project_id: Optional[int] = None) -> Optional[dict]:
    """Turn an HTTP error response into a structured error dict (None if OK)."""
    code = response.status_code
    if code < 400:
        return None

    messages = {
        401: "Authentication failed with SpecPilot API (401 Unauthorized)",
        403: "Access denied",
        404: "Project not found or access denied",
    }
    error = {
        "success": False,
        "error": messages.get(code, f"SpecPilot API returned an error: {code}"),
        "status_code": code,
    }
    if project_id is not None:
        error["project_id"] = project_id
    return error


def _auth_and_connection_error(exc: Exception, project_id: Optional[int] = None) -> dict:
    """Structured error for login/config/connection problems."""
    error: dict = {"success": False}
    if project_id is not None:
        error["project_id"] = project_id

    if isinstance(exc, AuthConfigError):
        error["error"] = str(exc)
    elif isinstance(exc, AuthLoginError):
        error["error"] = str(exc)
        error["status_code"] = 401
    else:
        error["error"] = "Could not connect to SpecPilot backend"
        error["details"] = str(exc)
    return error


_HANDLED = (AuthConfigError, AuthLoginError, httpx.RequestError)


def _bad_id(project_id: int) -> Optional[dict]:
    if project_id <= 0:
        return {
            "success": False,
            "project_id": project_id,
            "error": "project_id must be positive",
        }
    return None


async def _fetch_project(project_id: int):
    """
    GET /projects/{id}. This endpoint enforces ownership (404 for other
    users' projects), so every tool that returns project data goes
    through it first. Returns (project_dict, error_dict).
    """
    response = await authenticated_request("GET", f"/projects/{project_id}")
    error = _error_for_status(response, project_id)
    if error:
        return None, error

    data = response.json()
    if not isinstance(data, dict):
        return None, {
            "success": False,
            "project_id": project_id,
            "error": "Unexpected response from SpecPilot API",
        }
    return data, None


# ============================================================
# RENDERING HELPERS (pure functions: JSON-text fields -> Markdown)
# ============================================================

PRD_SECTIONS = [
    ("Product Overview", "product_overview"),
    ("Problem Statement", "prd_problem_statement"),
    ("Goals and Objectives", "goals_and_objectives"),
    ("Target Users", "prd_target_users"),
    ("Functional Requirements", "functional_requirements"),
    ("User Workflows", "user_workflows"),
    ("Business Rules", "business_rules"),
    ("Non-Functional Requirements", "non_functional_requirements"),
    ("Assumptions and Dependencies", "assumptions_and_dependencies"),
    ("Acceptance Criteria", "acceptance_criteria"),
]


def _parse(value):
    """Decode JSON stored as text; leave anything else untouched."""
    if isinstance(value, str):
        text = value.strip()
        if text[:1] in ("[", "{"):
            try:
                return json.loads(text)
            except ValueError:
                return value
    return value


def _is_empty(value) -> bool:
    value = _parse(value)
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in ("", "None", "Not specified")
    if isinstance(value, (list, tuple)):
        return all(_is_empty(v) for v in value)
    if isinstance(value, dict):
        return all(_is_empty(v) for v in value.values())
    return False


def _label(key: str) -> str:
    return str(key).replace("_", " ").capitalize()


def _render_item(item, indent: int) -> list:
    pad = "  " * indent

    if isinstance(item, str):
        return [f"{pad}- {item}"]

    if isinstance(item, dict):
        # Functional requirement: {id, requirement, source}
        if "id" in item and "requirement" in item:
            return [f"{pad}- **{item['id']}**: {item['requirement']}"]

        # Workflow: {name, actor, trigger, steps, expected_result}
        if "name" in item and ("steps" in item or "actor" in item):
            lines = [f"{pad}- **{item['name']}**"]
            for key in ("actor", "trigger"):
                if not _is_empty(item.get(key)):
                    lines.append(f"{pad}  - {_label(key)}: {item[key]}")
            steps = _parse(item.get("steps"))
            if isinstance(steps, list) and steps:
                lines.append(f"{pad}  - Steps:")
                for number, step in enumerate(steps, start=1):
                    lines.append(f"{pad}    {number}. {step}")
            if not _is_empty(item.get("expected_result")):
                lines.append(f"{pad}  - Expected result: {item['expected_result']}")
            return lines

        # Acceptance criteria: {requirement_id, criteria: [...]}
        if "requirement_id" in item and "criteria" in item:
            lines = [f"{pad}- **{item['requirement_id']}**"]
            criteria = _parse(item.get("criteria"))
            if isinstance(criteria, list):
                for criterion in criteria:
                    lines.append(f"{pad}  - {criterion}")
            else:
                lines.append(f"{pad}  - {criteria}")
            return lines

        # Any other dict (e.g. a sprint): title line, then its fields nested
        title_key = next(
            (
                k for k in ("name", "title", "sprint", "sprint_number", "id")
                if isinstance(item.get(k), (str, int)) and not _is_empty(item.get(k))
            ),
            None,
        )
        if title_key:
            prefix = "Sprint " if title_key in ("sprint", "sprint_number") else ""
            header = f"{pad}- **{prefix}{item[title_key]}**"
            rest = {k: v for k, v in item.items() if k != title_key}
        else:
            header = f"{pad}- **Item**"
            rest = item
        return [header, *_render(rest, indent + 1)]

    return [f"{pad}- {item}"]


def _render(value, indent: int = 0) -> list:
    """Render a decoded value as Markdown lines. Empty values give []."""
    pad = "  " * indent
    value = _parse(value)

    if _is_empty(value):
        return []

    if isinstance(value, str):
        return [pad + line for line in value.strip().splitlines()]

    if isinstance(value, list):
        lines = []
        for item in value:
            item = _parse(item)
            if _is_empty(item):
                continue
            lines.extend(_render_item(item, indent))
        return lines

    if isinstance(value, dict):
        lines = []
        for key, val in value.items():
            val = _parse(val)
            if _is_empty(val):
                continue
            if isinstance(val, (list, dict)):
                lines.append(f"{pad}- **{_label(key)}:**")
                lines.extend(_render(val, indent + 1))
            else:
                lines.append(f"{pad}- **{_label(key)}:** {val}")
        return lines

    return [f"{pad}{value}"]


def _safe_render(value) -> list:
    """_render with a fallback so an unexpected shape never crashes a tool."""
    try:
        return _render(value)
    except Exception:
        return ["```json", str(value), "```"]


def _has_prd(project: dict) -> bool:
    return any(not _is_empty(project.get(field)) for _, field in PRD_SECTIONS)


def _has_sprint_plan(project: dict) -> bool:
    return not _is_empty(project.get("sprint_plan"))


def build_prd_markdown(project: dict):
    """Return (markdown, missing_section_headings)."""
    name = project.get("project_name") or f"Project {project.get('id')}"
    parts = [f"# {name} - Product Requirements Document", ""]
    missing = []

    for heading, field in PRD_SECTIONS:
        body = _safe_render(project.get(field))
        if not body:
            missing.append(heading)
            continue
        parts.extend([f"## {heading}", "", *body, ""])

    if missing:
        parts.extend([
            "## Sections not specified",
            "",
            *[f"- {heading}" for heading in missing],
            "",
            "_These sections were left empty. Do not invent content for them._",
            "",
        ])

    return "\n".join(parts).rstrip() + "\n", missing


def build_sprint_markdown(project: dict) -> str:
    name = project.get("project_name") or f"Project {project.get('id')}"
    body = _safe_render(project.get("sprint_plan"))
    return "\n".join([f"# {name} - Sprint Plan", "", *body]).rstrip() + "\n"


def _sorted_tasks(tasks: list) -> list:
    return sorted(tasks, key=lambda t: t.get("id") or 0)


def build_tasks_markdown(tasks: list) -> str:
    lines = ["## Task Breakdown", ""]
    for number, task in enumerate(_sorted_tasks(tasks), start=1):
        label = task.get("task_number") or number
        meta = [
            task.get(key)
            for key in ("priority", "task_type", "module", "estimated_complexity", "status")
            if task.get(key)
        ]
        suffix = f"  _[{' | '.join(str(m) for m in meta)}]_" if meta else ""
        lines.append(f"### Task {label}: {task.get('task_title')}{suffix}")
        lines.append("")
        if not _is_empty(task.get("description")):
            lines.extend(_safe_render(task.get("description")))
            lines.append("")
        criteria = _safe_render(task.get("acceptance_criteria"))
        if criteria:
            lines.append("**Acceptance criteria:**")
            lines.extend(criteria)
            lines.append("")
        deps = _safe_render(task.get("dependencies"))
        if deps:
            lines.append("**Depends on:**")
            lines.extend(deps)
            lines.append("")
    if len(lines) == 2:
        lines.append("_No tasks have been generated yet._")
    return "\n".join(lines).rstrip() + "\n"


def _clean_task(task: dict, number: int) -> dict:
    """Task fields for tool output, with the dependencies text decoded."""
    dependencies = _parse(task.get("dependencies"))
    return {
        "number": task.get("task_number") or number,
        "id": task.get("id"),
        "task_title": task.get("task_title"),
        "description": task.get("description"),
        "task_type": task.get("task_type"),
        "module": task.get("module"),
        "priority": task.get("priority"),
        "acceptance_criteria": task.get("acceptance_criteria"),
        "owner_role": task.get("owner_role"),
        "dependencies": dependencies if isinstance(dependencies, list) else [],
        "estimated_complexity": task.get("estimated_complexity"),
        "status": task.get("status"),
        "source": task.get("source"),
    }


async def _fetch_tasks(project_id: int):
    """Tasks for a project the caller owns. Returns (project, tasks, error_dict)."""
    # /tasks/project/{id} itself has no ownership check, so ownership is
    # verified first through GET /projects/{id}.
    project, error = await _fetch_project(project_id)
    if error:
        return None, None, error

    response = await authenticated_request("GET", f"/tasks/project/{project_id}")
    error = _error_for_status(response, project_id)
    if error:
        return None, None, error

    tasks = response.json()
    if not isinstance(tasks, list):
        return None, None, {
            "success": False,
            "project_id": project_id,
            "error": "Unexpected response from SpecPilot API",
        }
    return project, _sorted_tasks(tasks), None


# ============================================================
# TOOLS
# ============================================================

@mcp.tool()
async def whoami() -> dict:
    """Show which SpecPilot account this connection is signed in as."""

    user = _current_user.get()
    if not user:
        return {"success": False, "error": "Not signed in to SpecPilot"}

    return {
        "success": True,
        "user_id": user.get("user_id"),
        "name": user.get("name"),
    }


@mcp.tool()
async def generate_project_spec(project_id: int) -> dict:
    """Run the existing SpecPilot project-generation pipeline."""

    bad = _bad_id(project_id)
    if bad:
        return bad

    try:
        # Ownership is verified first through GET /projects/{id}.
        _, error = await _fetch_project(project_id)
        if error:
            return error

        response = await authenticated_request(
            "POST",
            f"/generation/run/{project_id}",
            timeout=300.0,
        )

        error = _error_for_status(response, project_id)
        if error:
            error["details"] = response.text[:2000]
            return error

        try:
            data = response.json()
        except ValueError:
            return {
                "success": False,
                "project_id": project_id,
                "error": "Unexpected response from SpecPilot API",
            }

        return {
            "success": True,
            "project_id": project_id,
            "status": data.get("status"),
            "tasks_created": data.get("tasks_created"),
            "has_prd": bool(data.get("prd")),
            "has_sprint_plan": bool(data.get("sprint_plan")),
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc, project_id)


@mcp.tool()
async def list_projects() -> dict:
    """List the authenticated user's SpecPilot projects (id, name, category, PRD status)."""

    try:
        response = await authenticated_request("GET", "/projects/")

        error = _error_for_status(response)
        if error:
            return error

        projects = response.json()
        if not isinstance(projects, list):
            return {"success": False, "error": "Unexpected response from SpecPilot API"}

        return {
            "success": True,
            "count": len(projects),
            "projects": [
                {
                    "id": p.get("id"),
                    "project_name": p.get("project_name"),
                    "category": p.get("category"),
                    "has_prd": _has_prd(p),
                    "has_sprint_plan": _has_sprint_plan(p),
                }
                for p in projects
            ],
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc)


@mcp.tool()
async def get_project(project_id: int) -> dict:
    """Retrieve summary details and status for a project (no full PRD text)."""

    bad = _bad_id(project_id)
    if bad:
        return bad

    try:
        data, error = await _fetch_project(project_id)
        if error:
            return error

        return {
            "success": True,
            "id": data.get("id"),
            "project_name": data.get("project_name"),
            "category": data.get("category"),
            "overview": data.get("overview"),
            "business_objective": data.get("business_objective"),
            "target_users": data.get("target_users"),
            "problem_statement": data.get("problem_statement"),
            "proposed_solution": data.get("proposed_solution"),
            "target_audience": data.get("target_audience"),
            "business_value": data.get("business_value"),
            "technology_preferences": data.get("technology_preferences"),
            "has_prd": _has_prd(data),
            "has_sprint_plan": _has_sprint_plan(data),
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc, project_id)


@mcp.tool()
async def get_project_requirements(project_id: int) -> dict:
    """Get the requirement-interview answers, completeness status, and whether a PRD exists."""

    bad = _bad_id(project_id)
    if bad:
        return bad

    try:
        response = await authenticated_request("GET", f"/agent/requirements/{project_id}")

        error = _error_for_status(response, project_id)
        if error:
            return error

        data = response.json()
        return {
            "success": True,
            "project_id": data.get("project_id", project_id),
            "project_name": data.get("project_name"),
            "completeness_status": data.get("completeness_status"),
            "prd_generated": data.get("prd_generated"),
            "fields": data.get("fields"),
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc, project_id)


@mcp.tool()
async def get_project_prd(project_id: int) -> dict:
    """Get the full generated PRD as one clean Markdown document."""

    bad = _bad_id(project_id)
    if bad:
        return bad

    try:
        data, error = await _fetch_project(project_id)
        if error:
            return error

        if not _has_prd(data):
            return {
                "success": False,
                "project_id": project_id,
                "error": "No PRD has been generated for this project yet. "
                         "Run generate_project_spec first.",
            }

        markdown, missing = build_prd_markdown(data)
        return {
            "success": True,
            "project_id": project_id,
            "project_name": data.get("project_name"),
            "missing_sections": missing,
            "markdown": markdown,
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc, project_id)


@mcp.tool()
async def get_project_tasks(project_id: int) -> dict:
    """Get the generated task breakdown for a project, oldest first."""

    bad = _bad_id(project_id)
    if bad:
        return bad

    try:
        _, tasks, error = await _fetch_tasks(project_id)
        if error:
            return error

        return {
            "success": True,
            "project_id": project_id,
            "count": len(tasks),
            "tasks": [_clean_task(t, n) for n, t in enumerate(tasks, start=1)],
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc, project_id)


@mcp.tool()
async def get_sprint_plan(project_id: int) -> dict:
    """Get the generated sprint plan as Markdown."""

    bad = _bad_id(project_id)
    if bad:
        return bad

    try:
        data, error = await _fetch_project(project_id)
        if error:
            return error

        if not _has_sprint_plan(data):
            return {
                "success": False,
                "project_id": project_id,
                "error": "No sprint plan has been generated for this project yet. "
                         "Run generate_project_spec first.",
            }

        return {
            "success": True,
            "project_id": project_id,
            "project_name": data.get("project_name"),
            "markdown": build_sprint_markdown(data),
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc, project_id)


@mcp.tool()
async def get_build_brief(project_id: int) -> dict:
    """Get everything needed to build the app in one Markdown document: PRD, sprint plan, and tasks."""

    bad = _bad_id(project_id)
    if bad:
        return bad

    try:
        data, tasks, error = await _fetch_tasks(project_id)
        if error:
            return error

        if not _has_prd(data):
            return {
                "success": False,
                "project_id": project_id,
                "error": "No PRD has been generated for this project yet. "
                         "Run generate_project_spec first.",
            }

        prd_markdown, missing = build_prd_markdown(data)
        parts = [prd_markdown]

        if _has_sprint_plan(data):
            sprint = build_sprint_markdown(data).replace("# ", "## ", 1)
            parts.append(sprint)

        parts.append(build_tasks_markdown(tasks))

        technology = data.get("technology_preferences")
        header = []
        if not _is_empty(technology):
            header = [f"**Technology preferences:** {technology}", ""]

        return {
            "success": True,
            "project_id": project_id,
            "project_name": data.get("project_name"),
            "missing_sections": missing,
            "task_count": len(tasks),
            "markdown": "\n".join(header + ["\n".join(parts)]),
        }

    except _HANDLED as exc:
        return _auth_and_connection_error(exc, project_id)


# ============================================================
# SIGN-IN PROTECTION (applies to ALL tools)
# ============================================================
#
# Every request must carry a SpecPilot OAuth access token (obtained when the
# user signs in from Bolt). The token is checked by the SpecPilot backend
# (/oauth/exchange), which answers with a short-lived API token for that same
# user. The caller's own token is never forwarded to the API.
# ============================================================

class OAuthMiddleware:
    """Pure ASGI middleware: require a valid SpecPilot sign-in on every request."""

    def __init__(
        self,
        app,
        resource_url: str,
        issuer: str,
        backend_url: str,
        service_key: str,
    ):
        self.app = app
        self.resource_url = resource_url.rstrip("/")
        self.issuer = issuer.rstrip("/")
        self.backend_url = backend_url.rstrip("/")
        self.service_key = service_key

        parts = urlsplit(self.resource_url)
        self.metadata_url = (
            f"{parts.scheme}://{parts.netloc}"
            f"/.well-known/oauth-protected-resource{parts.path}"
        )

    async def _send_json(self, send, status: int, payload: dict, extra_headers=()):
        body = json.dumps(payload).encode()
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"cache-control", b"no-store"),
                *extra_headers,
            ],
        })
        await send({"type": "http.response.body", "body": body})

    async def _challenge(self, send, error: Optional[str] = None):
        value = f'Bearer resource_metadata="{self.metadata_url}", scope="specpilot"'
        if error:
            value += f', error="{error}"'
        await self._send_json(
            send,
            401,
            {"error": "Unauthorized"},
            [(b"www-authenticate", value.encode())],
        )

    async def _exchange(self, token: str):
        """Returns (user, api_token), or None when the token is not valid."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.backend_url}/oauth/exchange",
                json={"token": token},
                headers={"X-Service-Key": self.service_key},
            )

        if response.status_code == 401:
            return None

        if response.status_code != 200:
            raise RuntimeError(
                f"token exchange failed with status {response.status_code}"
            )

        data = response.json()
        user = {"user_id": data["user_id"], "name": data.get("name")}
        return user, data["api_token"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Discovery document: tells the client where to sign in (no login needed).
        if scope.get("path", "").startswith("/.well-known/oauth-protected-resource"):
            await self._send_json(send, 200, {
                "resource": self.resource_url,
                "authorization_servers": [self.issuer],
                "bearer_methods_supported": ["header"],
                "scopes_supported": ["specpilot"],
                "resource_name": "SpecPilot MCP Server",
            })
            return

        token = ""
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                scheme, _, rest = value.decode("latin-1").partition(" ")
                if scheme.lower() == "bearer":
                    token = rest.strip()
                break

        if not token:
            await self._challenge(send)
            return

        try:
            result = await self._exchange(token)
        except Exception as exc:
            logger.error("Sign-in check failed: %s", exc)
            await self._send_json(
                send,
                503,
                {"error": "Authentication service unavailable"},
            )
            return

        if result is None:
            await self._challenge(send, "invalid_token")
            return

        user, api_token = result

        user_reset = _current_user.set(user)
        token_reset = _api_token.set(api_token)
        try:
            await self.app(scope, receive, send)
        finally:
            _api_token.reset(token_reset)
            _current_user.reset(user_reset)


def _require_env(name: str, min_len: int = 1) -> str:
    value = (os.getenv(name) or "").strip()
    if len(value) < min_len:
        raise SystemExit(f"{name} environment variable is not set. Refusing to start.")
    return value


def build_app():
    resource_url = _require_env("MCP_RESOURCE_URL")
    issuer = _require_env("OAUTH_ISSUER")
    service_key = _require_env("MCP_SERVICE_KEY", 32)

    # When the server is reached through a tunnel, the Host header is the
    # tunnel's hostname (e.g. abc123.trycloudflare.com). List it in
    # MCP_ALLOWED_HOSTS (comma-separated, hostname only, no https://).
    extra_hosts = [
        h.strip()
        for h in os.getenv("MCP_ALLOWED_HOSTS", "").split(",")
        if h.strip()
    ]

    security = None
    if extra_hosts:
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:*", "localhost:*", *extra_hosts],
        )

    app = mcp.streamable_http_app(
        host="127.0.0.1",
        transport_security=security,
        json_response=True,
        stateless_http=True,
    )
    app.add_middleware(
        OAuthMiddleware,
        resource_url=resource_url,
        issuer=issuer,
        backend_url=SPEC_PILOT_API,
        service_key=service_key,
    )
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(build_app(), host="127.0.0.1", port=8100)