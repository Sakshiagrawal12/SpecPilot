"""
Deterministic facts read straight from source code (step 2 of the Code Spec feature).

Static analysis only: files are parsed with ast / json / regex and never executed
or imported. Every fact carries file:line so it can be checked against the code.

Python is supported first. JavaScript/React route and model detection comes later;
for now JS files only contribute dependencies and environment variable names.
"""

import ast
import json
import os
import re

try:
    import tomllib            # Python 3.11+
except ImportError:           # pragma: no cover
    tomllib = None


HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}

AUTH_HINTS = ("current_user", "get_current", "auth", "token", "login", "verify", "permission", "admin", "jwt")

FRAMEWORKS = {
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django", "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic", "alembic": "Alembic", "uvicorn": "Uvicorn", "gunicorn": "Gunicorn",
    "celery": "Celery", "pytest": "pytest", "jose": "python-jose (JWT)", "python-jose": "python-jose (JWT)",
    "passlib": "Passlib", "bcrypt": "bcrypt", "langchain": "LangChain", "langgraph": "LangGraph",
    "openai": "OpenAI SDK", "groq": "Groq SDK", "anthropic": "Anthropic SDK",
    "react": "React", "react-dom": "React", "vue": "Vue", "next": "Next.js", "express": "Express",
    "vite": "Vite", "tailwindcss": "Tailwind CSS", "typescript": "TypeScript", "jest": "Jest",
}

JS_LANGS = {"JavaScript", "React (JSX)", "TypeScript", "React (TSX)", "Vue", "Svelte"}

MAX_ROUTES = 1000
MAX_TESTS = 500
MAX_ENV = 200


# =========================================================
# SMALL AST HELPERS
# =========================================================

def _name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _bool_kw(call, key):
    for kw in call.keywords:
        if kw.arg == key and isinstance(kw.value, ast.Constant):
            return kw.value.value
    return None


def _unparse(node):
    try:
        return ast.unparse(node)
    except Exception:
        return None


# =========================================================
# ROUTES (FastAPI / Flask)
# =========================================================

def _router_prefixes(tree):
    prefixes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            fn = _name(node.value.func)
            if fn in ("APIRouter", "Blueprint"):
                prefix = ""
                for kw in node.value.keywords:
                    if kw.arg in ("prefix", "url_prefix"):
                        prefix = _str(kw.value) or ""
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        prefixes[t.id] = prefix
    return prefixes


def _requires_auth(func):
    """True if the handler depends on something that looks like authentication."""
    defaults = list(func.args.defaults) + [d for d in func.args.kw_defaults if d is not None]
    for d in defaults:
        if isinstance(d, ast.Call) and _name(d.func) == "Depends":
            text = (_unparse(d) or "").lower()
            if any(h in text for h in AUTH_HINTS):
                return True
    for dec in func.decorator_list:
        text = (_unparse(dec) or "").lower()
        if any(h in text for h in ("login_required", "jwt_required", "auth_required", "requires_auth")):
            return True
    return False


def _routes(tree, rel):
    prefixes = _router_prefixes(tree)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        auth = _requires_auth(node)
        for dec in node.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            attr = dec.func.attr
            if attr in HTTP_METHODS:
                methods = [attr.upper()]
            elif attr == "route":
                methods = ["GET"]
                for kw in dec.keywords:
                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        listed = [_str(e) for e in kw.value.elts if _str(e)]
                        if listed:
                            methods = [m.upper() for m in listed]
            else:
                continue

            path = _str(dec.args[0]) if dec.args else None
            if path is None:
                for kw in dec.keywords:
                    if kw.arg == "path":
                        path = _str(kw.value)
            # Only treat it as a route when the first argument looks like a URL path
            if path is None or not (path == "" or path.startswith("/")):
                continue

            owner = dec.func.value.id if isinstance(dec.func.value, ast.Name) else None
            full = prefixes.get(owner, "") + path
            for m in methods:
                found.append({
                    "method": m,
                    "path": full or "/",
                    "function": node.name,
                    "file": rel,
                    "line": dec.lineno,
                    "requires_auth": auth,
                })
    return found


# =========================================================
# DATABASE MODELS (SQLAlchemy declarative)
# =========================================================

def _column_info(name, call, annotation=None):
    typ, fk = None, None
    for a in call.args:
        if isinstance(a, ast.Call) and _name(a.func) == "ForeignKey":
            fk = _str(a.args[0]) if a.args else None
        elif typ is None and not isinstance(a, ast.Constant):
            typ = _unparse(a)
    if typ is None and annotation is not None:
        typ = _unparse(annotation)
    for kw in call.keywords:
        if kw.arg == "ForeignKey":
            continue
    return {
        "name": name,
        "type": typ,
        "primary_key": bool(_bool_kw(call, "primary_key")),
        "nullable": _bool_kw(call, "nullable"),
        "unique": bool(_bool_kw(call, "unique")),
        "foreign_key": fk,
    }


def _models(tree, rel):
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [_name(b) or "" for b in node.bases]
        if not any(b in ("Base", "Model", "DeclarativeBase") or b.endswith("Base") for b in bases):
            continue

        table, columns, relationships = None, [], []
        for stmt in node.body:
            target, value, annotation = None, None, None
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target, value = stmt.targets[0].id, stmt.value
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                target, value, annotation = stmt.target.id, stmt.value, stmt.annotation
            if target is None or value is None:
                continue

            if target == "__tablename__":
                table = _str(value)
            elif isinstance(value, ast.Call):
                fn = _name(value.func)
                if fn in ("Column", "mapped_column"):
                    columns.append(_column_info(target, value, annotation))
                elif fn == "relationship":
                    tgt = _str(value.args[0]) if value.args else None
                    relationships.append({"name": target, "target": tgt})

        if table is None:
            continue
        found.append({
            "class": node.name, "table": table, "file": rel, "line": node.lineno,
            "columns": columns, "relationships": relationships,
        })
    return found


# =========================================================
# TESTS, ENV VARS
# =========================================================

def _tests(tree, rel):
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            found.append({"file": rel, "name": node.name, "line": node.lineno})
    return found


def _py_env(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = _name(node.func)
            first = _str(node.args[0]) if node.args else None
            if first is None:
                continue
            if fn == "getenv":
                names.add(first)
            elif fn == "get" and isinstance(node.func, ast.Attribute) and _name(node.func.value) == "environ":
                names.add(first)
        elif isinstance(node, ast.Subscript) and _name(node.value) == "environ":
            key = _str(node.slice)
            if key:
                names.add(key)
    return names


_JS_ENV = re.compile(r"(?:process\.env|import\.meta\.env)\.([A-Za-z_][A-Za-z0-9_]*)")
_ENV_FILE_KEY = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


# =========================================================
# DEPENDENCIES
# =========================================================

_REQ = re.compile(r"^([A-Za-z0-9_.\-]+)\s*(\[[^\]]*\])?\s*(.*)$")


def _parse_requirement(line):
    line = line.split("#", 1)[0].strip().split(";", 1)[0].strip()
    if not line or line.startswith(("-", "git+", "http")):
        return None
    m = _REQ.match(line)
    if not m:
        return None
    return {"name": m.group(1).lower(), "spec": m.group(3).strip()}


def _read(src_dir, rel):
    with open(os.path.join(src_dir, *rel.split("/")), "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _deps_for(src_dir, rel):
    base = rel.rsplit("/", 1)[-1].lower()
    packages, ecosystem = [], None
    try:
        text = _read(src_dir, rel)
        if base == "requirements.txt":
            ecosystem = "python"
            packages = [p for p in (_parse_requirement(l) for l in text.splitlines()) if p]
        elif base == "pyproject.toml" and tomllib is not None:
            ecosystem = "python"
            data = tomllib.loads(text)
            for dep in data.get("project", {}).get("dependencies", []):
                p = _parse_requirement(dep)
                if p:
                    packages.append(p)
            poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for name, spec in poetry.items():
                if name.lower() != "python":
                    packages.append({"name": name.lower(), "spec": spec if isinstance(spec, str) else ""})
        elif base == "package.json":
            ecosystem = "node"
            data = json.loads(text)
            for key, dev in (("dependencies", False), ("devDependencies", True)):
                for name, spec in (data.get(key) or {}).items():
                    packages.append({"name": name, "spec": str(spec), "dev": dev})
    except Exception:
        return None
    if ecosystem is None:
        return None
    return {"file": rel, "ecosystem": ecosystem, "packages": packages}


# =========================================================
# MAIN ENTRY POINT
# =========================================================

def extract_facts(src_dir, inventory):
    routes, models, tests, parse_errors = [], [], [], []
    env_vars = set()
    test_set = set(inventory.get("test_files", []))

    for f in inventory["files"]:
        rel, lang = f["path"], f["language"]
        name = rel.rsplit("/", 1)[-1].lower()

        if lang == "Python":
            try:
                tree = ast.parse(_read(src_dir, rel))
            except Exception:
                parse_errors.append(rel)
                continue
            routes += _routes(tree, rel)
            models += _models(tree, rel)
            env_vars |= _py_env(tree)
            if rel in test_set:
                tests += _tests(tree, rel)

        elif lang in JS_LANGS:
            try:
                env_vars |= set(_JS_ENV.findall(_read(src_dir, rel)))
            except Exception:
                pass

        elif name in (".env.example", ".env.sample", ".env.template"):
            # variable NAMES only, values are never read into the result
            try:
                for line in _read(src_dir, rel).splitlines():
                    m = _ENV_FILE_KEY.match(line)
                    if m:
                        env_vars.add(m.group(1))
            except Exception:
                pass

    dependencies = []
    for path in inventory.get("key_files", []):
        d = _deps_for(src_dir, path)
        if d:
            dependencies.append(d)

    detected = set()
    for d in dependencies:
        for p in d["packages"]:
            label = FRAMEWORKS.get(p["name"])
            if label:
                detected.add(label)

    return {
        "frameworks": sorted(detected),
        "dependencies": dependencies,
        "routes": routes[:MAX_ROUTES],
        "models": models,
        "tests": tests[:MAX_TESTS],
        "env_vars": sorted(env_vars)[:MAX_ENV],
        "parse_errors": parse_errors,
        "notes": [
            "Routes and models are found by static analysis of Python code (FastAPI, Flask, SQLAlchemy).",
            "A route's auth flag is a heuristic based on dependency names, not a security audit.",
            "Router prefixes added in include_router(...) are not included in route paths.",
            "JavaScript routes and components are not analysed yet.",
        ],
    }