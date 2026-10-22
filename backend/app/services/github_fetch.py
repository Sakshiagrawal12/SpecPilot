"""
Download a PUBLIC GitHub repository as a ZIP (step 1b of the Code Spec feature).

Safety:
  - only github.com links are accepted
  - requests go only to api.github.com / codeload.github.com (redirects are checked too)
  - download size is capped while streaming
Nothing from the repository is executed.
"""

import os
import re
import urllib.error
import urllib.request
from urllib.parse import quote, urlparse


ALLOWED_HOSTS = {"api.github.com", "codeload.github.com"}

_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
_REF = re.compile(r"^[A-Za-z0-9_./-]{1,200}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_\-]{20,255}$")


class GithubError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


# =========================================================
# URL PARSING
# =========================================================

def parse_github_url(url):
    """
    Accepts:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      https://github.com/owner/repo/tree/some-branch
      github.com/owner/repo
    Returns (owner, repo, ref_or_None).
    """
    url = (url or "").strip()
    if url.lower().startswith("github.com/") or url.lower().startswith("www.github.com/"):
        url = "https://" + url

    p = urlparse(url)
    if p.scheme not in ("http", "https") or (p.hostname or "").lower() not in ("github.com", "www.github.com"):
        raise GithubError("Only github.com links are supported.")

    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2:
        raise GithubError("Use a link like https://github.com/owner/repo")

    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not _NAME.match(owner) or not _NAME.match(repo):
        raise GithubError("That does not look like a valid GitHub repository link.")

    ref = None
    if len(parts) >= 4 and parts[2] == "tree":
        ref = "/".join(parts[3:])
        if not _REF.match(ref) or ".." in ref:
            raise GithubError("That branch name is not valid.")

    return owner, repo, ref


# =========================================================
# DOWNLOAD
# =========================================================

class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    """GitHub redirects the zipball to codeload.github.com. Allow only that."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urlparse(newurl)
        if p.scheme != "https" or (p.hostname or "").lower() not in ALLOWED_HOSTS:
            raise GithubError("GitHub redirected to an unexpected address.", 502)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_token(token):
    """A user-supplied personal access token: used for ONE download, never stored or logged."""
    token = (token or "").strip()
    if not token:
        return None
    if not _TOKEN.match(token):
        raise GithubError("That access token does not look valid. Paste only the token itself.")
    return token


def download_repo_zip(owner, repo, ref, dest_path, max_bytes, timeout=60, token=None):
    """
    Download the repo (default branch when ref is None) to dest_path.

    token: the user's own personal access token for a private repository.
    When given it is used instead of any server-wide GITHUB_TOKEN.
    """
    api = f"https://api.github.com/repos/{owner}/{repo}/zipball"
    if ref:
        api += "/" + quote(ref, safe="/")

    headers = {"User-Agent": "SpecPilot", "Accept": "application/vnd.github+json"}
    if not token:
        token = os.getenv("GITHUB_TOKEN")  # optional server token: only for raising the public rate limit
    if token:
        headers["Authorization"] = "Bearer " + token

    opener = urllib.request.build_opener(_SafeRedirect)

    try:
        resp = opener.open(urllib.request.Request(api, headers=headers), timeout=timeout)
    except GithubError:
        raise
    except urllib.error.HTTPError as e:
        # 400 (not 401) for token problems, so a front end never mistakes it for an expired login
        if e.code == 401:
            raise GithubError("GitHub rejected the access token. It may be wrong, expired or revoked.", 400)
        if e.code == 404:
            if token:
                raise GithubError(
                    "Repository or branch not found, or the access token has no permission to read it.", 404)
            raise GithubError(
                "Repository or branch not found, or it is private. "
                "For a private repository, tick the private option and add an access token.", 404)
        if e.code in (403, 429):
            raise GithubError("GitHub is limiting requests right now. Try again in a few minutes.", 429)
        raise GithubError(f"GitHub returned an error ({e.code}).", 502)
    except OSError:
        raise GithubError("Could not reach GitHub from the server.", 502)

    with resp:
        length = resp.headers.get("Content-Length")
        if length and length.isdigit() and int(length) > max_bytes:
            raise GithubError(
                f"This repository is too large (limit {max_bytes // (1024 * 1024)} MB).", 413)

        size = 0
        try:
            with open(dest_path, "wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise GithubError(
                            f"This repository is too large (limit {max_bytes // (1024 * 1024)} MB).", 413)
                    out.write(chunk)
        except OSError:
            raise GithubError("The download from GitHub was interrupted.", 502)

    return size