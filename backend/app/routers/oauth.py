"""
OAuth 2.1 authorization server for the SpecPilot MCP server.

What it does
------------
1. Publishes discovery metadata        GET  /.well-known/oauth-authorization-server
2. Registers MCP clients (Bolt, ...)   POST /oauth/register
3. Shows the SpecPilot sign-in page    GET  /oauth/authorize
   and, after sign-in, issues a code   POST /oauth/authorize
4. Trades code + PKCE for tokens       POST /oauth/token
5. Lets the MCP server swap a valid MCP token for a short-lived API token
   for that same user (no token passthrough) POST /oauth/exchange

Environment variables
---------------------
OAUTH_ISSUER       public https address of THIS backend, e.g. https://abc.trycloudflare.com
MCP_RESOURCE_URL   public https address of the MCP endpoint, e.g. https://xyz.trycloudflare.com/mcp
OAUTH_SIGNING_KEY  random secret (32+ chars) used only for MCP access tokens
MCP_SERVICE_KEY   random secret (32+ chars) shared with the MCP server for /oauth/exchange

OAUTH_SIGNING_KEY must differ from the key in app/auth.py, so an MCP token can
never be accepted by the normal API.
"""

import base64
import hashlib
import hmac
import html
import os
import re
import secrets
import time
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import bcrypt
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import ALGORITHM, SECRET_KEY
from app.database import get_db
from app.models import OAuthAuthCode, OAuthClient, OAuthRefreshToken, User

router = APIRouter(tags=["OAuth"])

SCOPE = "specpilot"
CODE_TTL_SECONDS = 300
ACCESS_TTL_SECONDS = 3600
REFRESH_TTL_SECONDS = 30 * 24 * 3600
EXCHANGE_TOKEN_MINUTES = 10
MAX_CLIENTS = 5000
MAX_LOGIN_FAILURES = 5
LOGIN_WINDOW_SECONDS = 300

NO_STORE = {"Cache-Control": "no-store", "Pragma": "no-cache"}
CORS = {"Access-Control-Allow-Origin": "*"}

CHALLENGE_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
VERIFIER_RE = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")

AUTH_PARAMS = [
    "response_type",
    "client_id",
    "redirect_uri",
    "code_challenge",
    "code_challenge_method",
    "state",
    "resource",
    "scope",
]


# =========================================================
# CONFIGURATION
# =========================================================

def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _need_env(name: str, min_len: int = 1) -> str:
    value = _env(name)
    if len(value) < min_len:
        raise HTTPException(
            status_code=503,
            detail=f"OAuth is not configured: set {name}",
        )
    return value


def _issuer() -> str:
    return _need_env("OAUTH_ISSUER").rstrip("/")


def _resource() -> str:
    return _need_env("MCP_RESOURCE_URL").rstrip("/")


def _signing_key() -> str:
    key = _need_env("OAUTH_SIGNING_KEY", 32)
    if key == SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="OAUTH_SIGNING_KEY must be different from the API JWT key",
        )
    return key


# =========================================================
# SMALL HELPERS
# =========================================================

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json(data: dict, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status, headers={**NO_STORE, **CORS})


def _oauth_error(error: str, description: str, status: int = 400) -> JSONResponse:
    return _json(
        {"error": error, "error_description": description},
        status,
    )


def _redirect(uri: str, **params) -> RedirectResponse:
    parts = urlsplit(uri)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query += [(k, v) for k, v in params.items() if v is not None]

    return RedirectResponse(
        urlunsplit(parts._replace(query=urlencode(query))),
        status_code=303,
        headers=NO_STORE,
    )


def _valid_redirect_uri(uri: str) -> bool:
    try:
        parts = urlsplit(uri)
    except ValueError:
        return False

    if parts.fragment or not parts.netloc:
        return False

    if parts.scheme == "https":
        return True

    return parts.scheme == "http" and parts.hostname in (
        "localhost",
        "127.0.0.1",
        "::1",
    )


def _pkce_ok(verifier: str, challenge: str) -> bool:
    if not VERIFIER_RE.match(verifier or ""):
        return False

    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    return hmac.compare_digest(expected, challenge)


# =========================================================
# LOGIN PROTECTION (password check + attempt limit)
# =========================================================

_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())
_failures: dict = {}


def _check_password(password: str, stored_hash: Optional[str]) -> bool:
    # Unknown users still run a bcrypt check, so timing does not reveal them.
    try:
        target = stored_hash.encode("utf-8") if stored_hash else _DUMMY_HASH
        valid = bcrypt.checkpw(password.encode("utf-8"), target)
    except ValueError:
        return False

    return bool(stored_hash) and valid


def _locked(key: str) -> bool:
    now = time.time()
    recent = [t for t in _failures.get(key, []) if now - t < LOGIN_WINDOW_SECONDS]
    _failures[key] = recent
    return len(recent) >= MAX_LOGIN_FAILURES


def _record_failure(key: str) -> None:
    if len(_failures) > 10000:
        _failures.clear()
    _failures.setdefault(key, []).append(time.time())


# =========================================================
# SIGN-IN PAGE
# =========================================================

PAGE_CSS = """
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#eef1f4;font:16px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif;color:#1d2230}
main{background:#fff;border:1px solid #d6d9e0;border-radius:10px;padding:28px;width:min(420px,92vw)}
h1{font-size:22px;margin:0 0 6px}
p{margin:0 0 16px;color:#4b5363}
label{display:block;font-size:14px;margin:12px 0 4px}
input{width:100%;box-sizing:border-box;padding:10px;font:inherit;border:1px solid #c5cad3;border-radius:6px}
input:focus-visible,button:focus-visible{outline:2px solid #4f46e5;outline-offset:2px}
.row{display:flex;gap:10px;margin-top:20px}
button{flex:1;padding:10px;font:inherit;border-radius:6px;cursor:pointer;border:1px solid #c5cad3;background:#fff;color:inherit}
button.primary{background:#4f46e5;border-color:#4f46e5;color:#fff}
.err{background:#fbe9e7;color:#b3261e;padding:8px 10px;border-radius:6px;margin:12px 0 0;font-size:14px}
"""


def _page(title: str, body: str, status: int = 200) -> HTMLResponse:
    document = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>{PAGE_CSS}</style></head>"
        f"<body><main>{body}</main></body></html>"
    )

    return HTMLResponse(
        document,
        status_code=status,
        headers={
            **NO_STORE,
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": (
                "default-src 'none'; style-src 'unsafe-inline'; "
                "frame-ancestors 'none'; base-uri 'none'"
            ),
        },
    )


def _login_page(
    client: OAuthClient,
    params: dict,
    error: Optional[str] = None,
    status: int = 200,
) -> HTMLResponse:
    hidden = "".join(
        f"<input type='hidden' name='{name}' value='{html.escape(params[name], quote=True)}'>"
        for name in AUTH_PARAMS
    )

    error_html = f"<div class='err' role='alert'>{html.escape(error)}</div>" if error else ""

    body = (
        "<h1>Sign in to SpecPilot</h1>"
        f"<p><strong>{html.escape(client.client_name)}</strong> wants to read and manage "
        "your SpecPilot projects, requirements, PRDs, tasks and sprint plans.</p>"
        "<form method='post' action='/oauth/authorize'>"
        f"{hidden}"
        "<label for='email'>Email</label>"
        "<input id='email' name='email' type='email' required autofocus autocomplete='username'>"
        "<label for='password'>Password</label>"
        "<input id='password' name='password' type='password' required autocomplete='current-password'>"
        f"{error_html}"
        "<div class='row'>"
        "<button type='submit' name='decision' value='deny' formnovalidate>Cancel</button>"
        "<button type='submit' name='decision' value='allow' class='primary'>Sign in and allow</button>"
        "</div></form>"
    )

    return _page("Sign in to SpecPilot", body, status)


def _validate_authorize(db: Session, p: dict):
    """Returns (client, error_response). error_response is None when valid."""

    client = (
        db.query(OAuthClient)
        .filter(OAuthClient.client_id == p["client_id"])
        .first()
    )

    # An unknown client or redirect address is never redirected to.
    if client is None or p["redirect_uri"] not in (client.redirect_uris or []):
        return None, _page(
            "Cannot continue",
            "<h1>Cannot continue</h1><p>This sign-in request is not valid: "
            "unknown application or redirect address.</p>",
            400,
        )

    def fail(error: str, description: str):
        return _redirect(
            p["redirect_uri"],
            error=error,
            error_description=description,
            state=p["state"] or None,
            iss=_issuer(),
        )

    if p["response_type"] != "code":
        return client, fail("unsupported_response_type", "Only response_type=code is supported.")

    if p["code_challenge_method"] != "S256" or not CHALLENGE_RE.match(p["code_challenge"]):
        return client, fail("invalid_request", "PKCE with S256 is required.")

    if p["resource"] and p["resource"].rstrip("/") != _resource():
        return client, fail("invalid_target", "Unknown resource.")

    return client, None


# =========================================================
# 1. DISCOVERY
# =========================================================

@router.get("/.well-known/oauth-authorization-server")
def authorization_server_metadata():
    issuer = _issuer()

    return _json({
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/oauth/authorize",
        "token_endpoint": f"{issuer}/oauth/token",
        "registration_endpoint": f"{issuer}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": [SCOPE],
        "authorization_response_iss_parameter_supported": True,
    })


# =========================================================
# 2. CLIENT REGISTRATION (RFC 7591)
# =========================================================

class RegistrationRequest(BaseModel):
    redirect_uris: List[str]
    client_name: Optional[str] = None
    token_endpoint_auth_method: Optional[str] = "none"
    grant_types: Optional[List[str]] = None
    response_types: Optional[List[str]] = None


@router.post("/oauth/register")
def register_client(
    body: RegistrationRequest,
    db: Session = Depends(get_db),
):
    uris = body.redirect_uris

    if not uris or len(uris) > 5 or not all(_valid_redirect_uri(u) for u in uris):
        return _oauth_error(
            "invalid_redirect_uri",
            "Provide 1 to 5 redirect URIs. Each must use https (or http on localhost) and have no fragment.",
        )

    if body.token_endpoint_auth_method not in (None, "none"):
        return _oauth_error(
            "invalid_client_metadata",
            "Only public clients are supported (token_endpoint_auth_method 'none').",
        )

    if db.query(OAuthClient).count() >= MAX_CLIENTS:
        return _oauth_error(
            "temporarily_unavailable",
            "Too many registered clients.",
            429,
        )

    name = (body.client_name or "").strip()[:100] or "MCP client"

    client = OAuthClient(
        client_id="sp_" + secrets.token_urlsafe(16),
        client_name=name,
        redirect_uris=uris,
    )

    db.add(client)
    db.commit()

    return _json(
        {
            "client_id": client.client_id,
            "client_name": client.client_name,
            "redirect_uris": client.redirect_uris,
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "client_id_issued_at": int(time.time()),
        },
        201,
    )


# =========================================================
# 3. AUTHORIZATION (sign-in page)
# =========================================================

@router.get("/oauth/authorize")
def authorize_form(
    request: Request,
    db: Session = Depends(get_db),
):
    params = {name: request.query_params.get(name, "") for name in AUTH_PARAMS}

    client, error = _validate_authorize(db, params)

    if error is not None:
        return error

    return _login_page(client, params)


@router.post("/oauth/authorize")
def authorize_submit(
    response_type: str = Form(""),
    client_id: str = Form(""),
    redirect_uri: str = Form(""),
    code_challenge: str = Form(""),
    code_challenge_method: str = Form(""),
    state: str = Form(""),
    resource: str = Form(""),
    scope: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    decision: str = Form("allow"),
    db: Session = Depends(get_db),
):
    params = {
        "response_type": response_type,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "state": state,
        "resource": resource,
        "scope": scope,
    }

    client, error = _validate_authorize(db, params)

    if error is not None:
        return error

    if decision == "deny":
        return _redirect(
            redirect_uri,
            error="access_denied",
            state=state or None,
            iss=_issuer(),
        )

    email_key = email.strip().lower()

    if _locked(email_key):
        return _login_page(
            client,
            params,
            "Too many attempts. Please wait a few minutes and try again.",
            429,
        )

    user = db.query(User).filter(User.email == email_key).first()

    if not _check_password(password, user.password_hash if user else None):
        _record_failure(email_key)
        return _login_page(client, params, "Invalid email or password.", 401)

    _failures.pop(email_key, None)

    code = secrets.token_urlsafe(32)

    db.add(
        OAuthAuthCode(
            code_hash=_sha256(code),
            client_id=client.client_id,
            user_id=user.id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            resource=_resource(),
            scope=SCOPE,
            expires_at=datetime.utcnow() + timedelta(seconds=CODE_TTL_SECONDS),
        )
    )
    db.commit()

    return _redirect(
        redirect_uri,
        code=code,
        state=state or None,
        iss=_issuer(),
    )


# =========================================================
# 4. TOKEN ENDPOINT
# =========================================================

def _issue_tokens(
    db: Session,
    client_id: str,
    user_id: int,
    resource: str,
    scope: str,
) -> JSONResponse:
    now = int(time.time())

    access_token = jwt.encode(
        {
            "iss": _issuer(),
            "sub": str(user_id),
            "aud": resource,
            "iat": now,
            "exp": now + ACCESS_TTL_SECONDS,
            "jti": secrets.token_hex(8),
            "client_id": client_id,
            "scope": scope,
        },
        _signing_key(),
        algorithm="HS256",
    )

    refresh_token = secrets.token_urlsafe(48)

    db.add(
        OAuthRefreshToken(
            token_hash=_sha256(refresh_token),
            client_id=client_id,
            user_id=user_id,
            resource=resource,
            scope=scope,
            expires_at=datetime.utcnow() + timedelta(seconds=REFRESH_TTL_SECONDS),
        )
    )
    db.commit()

    return _json({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TTL_SECONDS,
        "refresh_token": refresh_token,
        "scope": scope,
    })


@router.post("/oauth/token")
def token_endpoint(
    grant_type: str = Form(""),
    code: str = Form(""),
    redirect_uri: str = Form(""),
    client_id: str = Form(""),
    code_verifier: str = Form(""),
    refresh_token: str = Form(""),
    resource: str = Form(""),
    db: Session = Depends(get_db),
):
    client = (
        db.query(OAuthClient)
        .filter(OAuthClient.client_id == client_id)
        .first()
    )

    if client is None:
        return _oauth_error("invalid_client", "Unknown client.", 401)

    if resource and resource.rstrip("/") != _resource():
        return _oauth_error("invalid_target", "Unknown resource.")

    # ---------------------------------------------------------
    # authorization_code
    # ---------------------------------------------------------
    if grant_type == "authorization_code":

        code_hash = _sha256(code)

        # Burn the code atomically: it can be used exactly once.
        burned = (
            db.query(OAuthAuthCode)
            .filter(
                OAuthAuthCode.code_hash == code_hash,
                OAuthAuthCode.used == False,  # noqa: E712
            )
            .update({"used": True})
        )
        db.commit()

        row = (
            db.query(OAuthAuthCode)
            .filter(OAuthAuthCode.code_hash == code_hash)
            .first()
        )

        if (
            not burned
            or row is None
            or row.expires_at < datetime.utcnow()
            or row.client_id != client.client_id
            or row.redirect_uri != redirect_uri
            or not _pkce_ok(code_verifier, row.code_challenge)
        ):
            return _oauth_error("invalid_grant", "The authorization code is invalid or expired.")

        return _issue_tokens(db, client.client_id, row.user_id, row.resource, row.scope)

    # ---------------------------------------------------------
    # refresh_token (rotated on every use)
    # ---------------------------------------------------------
    if grant_type == "refresh_token":

        row = (
            db.query(OAuthRefreshToken)
            .filter(OAuthRefreshToken.token_hash == _sha256(refresh_token))
            .first()
        )

        if row is None or row.client_id != client.client_id:
            return _oauth_error("invalid_grant", "The refresh token is invalid.")

        if row.revoked:
            # An old token was used again: assume it leaked and end the whole family.
            (
                db.query(OAuthRefreshToken)
                .filter(
                    OAuthRefreshToken.client_id == row.client_id,
                    OAuthRefreshToken.user_id == row.user_id,
                    OAuthRefreshToken.revoked == False,  # noqa: E712
                )
                .update({"revoked": True})
            )
            db.commit()
            return _oauth_error("invalid_grant", "The refresh token is invalid.")

        if row.expires_at < datetime.utcnow():
            return _oauth_error("invalid_grant", "The refresh token has expired.")

        user = db.query(User).filter(User.id == row.user_id).first()

        if user is None:
            return _oauth_error("invalid_grant", "The account no longer exists.")

        row.revoked = True
        db.commit()

        return _issue_tokens(db, row.client_id, row.user_id, row.resource, row.scope)

    return _oauth_error("unsupported_grant_type", "Unsupported grant_type.")


# =========================================================
# 5. EXCHANGE (called only by the MCP server)
# =========================================================
#
# The MCP server must not forward the caller's MCP token to the API. It
# sends the token here instead; if it is valid, the backend answers with a
# short-lived API token for that same user.
# =========================================================

class ExchangeRequest(BaseModel):
    token: str


@router.post("/oauth/exchange")
def exchange_token(
    body: ExchangeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    expected = _need_env("MCP_SERVICE_KEY", 32)
    provided = request.headers.get("x-service-key", "")

    if not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        claims = jwt.decode(
            body.token,
            _signing_key(),
            algorithms=["HS256"],
            audience=_resource(),
            issuer=_issuer(),
        )
        user_id = int(claims["sub"])
    except (JWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires = datetime.utcnow() + timedelta(minutes=EXCHANGE_TOKEN_MINUTES)

    api_token = jwt.encode(
        {"sub": str(user.id), "exp": expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "user_id": user.id,
        "name": user.name,
        "api_token": api_token,
        "expires_in": EXCHANGE_TOKEN_MINUTES * 60,
    }