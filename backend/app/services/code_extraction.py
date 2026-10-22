"""
Safe ZIP extraction and file inventory (step 1 of the Code Spec feature).

Static only: nothing from the upload is ever executed or imported.
"""

import os
import zipfile
from collections import Counter, defaultdict


# =========================================================
# LIMITS
# =========================================================

MAX_UPLOAD_BYTES = 50 * 1024 * 1024      # size of the ZIP itself
MAX_ENTRIES = 50_000                      # entries inside the ZIP (node_modules can be large)
MAX_KEPT_FILES = 5_000                    # source files we keep after filtering
MAX_FILE_BYTES = 1 * 1024 * 1024          # per-file cap; bigger files are skipped
MAX_TOTAL_BYTES = 100 * 1024 * 1024       # total uncompressed bytes we keep


class ExtractionError(Exception):
    """Raised for anything the user should be told about (bad ZIP, unsafe, too big)."""


# =========================================================
# FILTERS
# =========================================================

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "venv", ".venv", "env", ".env.d",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "dist", "build", ".next", ".nuxt", ".cache", ".idea", ".vscode",
    "target", "vendor", "site-packages", "coverage", ".gradle", "bower_components",
}

BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svgz", ".tiff",
    ".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi", ".webm", ".ogg",
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".class", ".jar", ".pyc", ".pyo",
    ".db", ".sqlite", ".sqlite3", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".lock",
}

SECRET_EXT = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"}

SECRET_NAMES = {
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credentials.json", "secrets.json",
    "service-account.json", ".npmrc", ".pypirc", ".netrc",
}

ENV_ALLOWED = {".env.example", ".env.sample", ".env.template"}   # names only, no real values

LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "React (JSX)", ".mjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "React (TSX)", ".vue": "Vue", ".svelte": "Svelte",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".json": "JSON", ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML",
    ".sql": "SQL", ".java": "Java", ".go": "Go", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".c": "C", ".h": "C/C++ header", ".cpp": "C++", ".rs": "Rust",
    ".sh": "Shell", ".xml": "XML", ".txt": "Text", ".ini": "Config", ".cfg": "Config",
}

KEY_FILE_NAMES = {
    "requirements.txt", "pyproject.toml", "setup.py", "pipfile", "package.json",
    "tsconfig.json", "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "pom.xml", "build.gradle", "go.mod", "cargo.toml", "composer.json", "gemfile",
    "vite.config.js", "vite.config.ts", "next.config.js", "alembic.ini", "pytest.ini",
    ".env.example", ".env.sample", "readme.md", "readme.txt", "readme",
}


# =========================================================
# HELPERS
# =========================================================

def _clean_parts(name):
    """Split an archive path into safe parts, or return None if it is unsafe."""
    name = name.replace("\\", "/")
    if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        return None
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if ".." in parts:
        return None
    return parts


def _is_symlink(info):
    mode = (info.external_attr >> 16) & 0o170000
    return mode == 0o120000


def _language(filename):
    low = filename.lower()
    if low == "dockerfile":
        return "Dockerfile"
    if low == "makefile":
        return "Makefile"
    return LANGUAGES.get(os.path.splitext(low)[1], "Other")


def _skip_reason(parts):
    """Why a file should not be kept, or None to keep it."""
    for d in parts[:-1]:
        dl = d.lower()
        if dl in SKIP_DIRS or dl.endswith(".egg-info"):
            return "ignored folder"
    name = parts[-1].lower()
    ext = os.path.splitext(name)[1]
    if name.startswith(".env") and name not in ENV_ALLOWED:
        return "secret file"
    if name in SECRET_NAMES or name.startswith("id_rsa") or ext in SECRET_EXT:
        return "secret file"
    if ext in BINARY_EXT:
        return "binary file"
    return None


def _is_test_file(parts):
    name = parts[-1].lower()
    in_test_dir = any(p.lower() in ("tests", "test", "__tests__") for p in parts[:-1])
    return (
        in_test_dir
        or name.startswith("test_")
        or name.endswith(("_test.py", ".test.js", ".test.jsx", ".test.ts", ".test.tsx",
                          ".spec.js", ".spec.jsx", ".spec.ts", ".spec.tsx"))
    )


def _copy_limited(src, dest_path, limit):
    """Copy a stream to disk, counting REAL bytes (the ZIP header size can lie)."""
    written = 0
    with open(dest_path, "wb") as out:
        while True:
            chunk = src.read(64 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > limit:
                return None
            out.write(chunk)
    return written


# =========================================================
# MAIN ENTRY POINT
# =========================================================

def extract_zip(zip_path, dest_dir):
    """
    Safely extract the source files of a ZIP into dest_dir and return an inventory.

    Raises ExtractionError for invalid, password-protected, unsafe or oversized archives.
    """
    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile:
        raise ExtractionError("This is not a valid ZIP file.")

    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ExtractionError(f"The ZIP has too many entries (limit {MAX_ENTRIES}).")

        # ---- pass 1: validate paths, find the shared root folder ----
        entries = []
        for info in infos:
            parts = _clean_parts(info.filename)
            if parts is None:
                raise ExtractionError(f"Unsafe path in ZIP: {info.filename!r}")
            if info.is_dir() or not parts:
                continue
            if info.flag_bits & 0x1:
                raise ExtractionError("Password-protected ZIP files are not supported.")
            entries.append((info, parts))

        root_stripped = None
        if entries and all(len(p) > 1 for _, p in entries) and len({p[0] for _, p in entries}) == 1:
            root_stripped = entries[0][1][0]
            entries = [(i, p[1:]) for i, p in entries]

        # ---- pass 2: filter and extract ----
        os.makedirs(dest_dir, exist_ok=True)
        root_real = os.path.realpath(dest_dir)

        skipped = Counter()
        files = []
        lang_files = Counter()
        lang_lines = defaultdict(int)
        key_files, test_files = [], []
        total_bytes = 0
        total_lines = 0

        for info, parts in entries:
            if _is_symlink(info):
                skipped["symlink"] += 1
                continue

            reason = _skip_reason(parts)
            if reason:
                skipped[reason] += 1
                continue

            if info.file_size > MAX_FILE_BYTES:
                skipped["too large"] += 1
                continue

            if len(files) >= MAX_KEPT_FILES:
                raise ExtractionError(f"Too many source files (limit {MAX_KEPT_FILES}). "
                                      "Remove generated or vendored folders and try again.")

            target = os.path.realpath(os.path.join(dest_dir, *parts))
            if os.path.commonpath([root_real, target]) != root_real:
                raise ExtractionError(f"Unsafe path in ZIP: {info.filename!r}")

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zf.open(info) as src:
                size = _copy_limited(src, target, MAX_FILE_BYTES)
            if size is None:
                os.remove(target)
                skipped["too large"] += 1
                continue

            total_bytes += size
            if total_bytes > MAX_TOTAL_BYTES:
                raise ExtractionError("The extracted source is too large (limit 100 MB).")

            with open(target, "rb") as f:
                data = f.read()
            if b"\0" in data[:2048]:
                os.remove(target)
                total_bytes -= size
                skipped["binary file"] += 1
                continue

            lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
            rel = "/".join(parts)
            lang = _language(parts[-1])

            files.append({"path": rel, "language": lang, "size": size, "lines": lines})
            lang_files[lang] += 1
            lang_lines[lang] += lines
            total_lines += lines

            if parts[-1].lower() in KEY_FILE_NAMES:
                key_files.append(rel)
            if _is_test_file(parts):
                test_files.append(rel)

    files.sort(key=lambda f: f["path"])
    languages = sorted(
        ({"language": l, "files": lang_files[l], "lines": lang_lines[l]} for l in lang_files),
        key=lambda x: x["lines"], reverse=True,
    )

    return {
        "root_folder": root_stripped,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "total_lines": total_lines,
        "languages": languages,
        "key_files": sorted(key_files),
        "test_files": sorted(test_files)[:200],
        "skipped": dict(skipped),
        "files": files,
    }