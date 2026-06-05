"""GitHub Release-based skill distribution.

Downloads and caches skills-bundle.tar.gz from GitHub Releases.
Cache location: ~/.quivo/cache/{release_tag}/
"""

from __future__ import annotations

import os
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.prompt import Prompt

console = Console()

DEFAULT_REPO = "chordpli/quivo"
BUNDLE_ASSET = "skills-bundle.tar.gz"
CACHE_BASE = Path.home() / ".quivo" / "cache"
TOKEN_FILE = Path.home() / ".quivo" / "token"
CONFIG_FILENAME = "quivo.yml"


def _find_repo_config() -> Optional[str]:
    """Walk up from the cwd looking for a committed ``quivo.yml`` with a
    top-level ``repo:`` key. This lets a forked repo declare its own skill
    source once, so engineers never need to set QUIVO_REPO by hand.
    """
    import yaml

    cur = Path.cwd()
    for d in [cur, *cur.parents]:
        cfg = d / CONFIG_FILENAME
        if cfg.is_file():
            try:
                data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
            except Exception:
                return None
            repo = data.get("repo")
            if isinstance(repo, str) and repo.strip():
                return repo.strip()
    return None


def _repo() -> str:
    """Resolve the skills repo: env override > repo-root quivo.yml > default."""
    return os.environ.get("QUIVO_REPO") or _find_repo_config() or DEFAULT_REPO


def _read_token_file() -> Optional[str]:
    if TOKEN_FILE.is_file():
        try:
            t = TOKEN_FILE.read_text(encoding="utf-8").strip()
            return t or None
        except OSError:
            return None
    return None


def _get_token() -> Optional[str]:
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or _read_token_file()


def _auth_headers() -> dict[str, str]:
    token = _get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _prompt_and_save_token() -> Optional[str]:
    """Prompt user for a GitHub token, persist to ~/.quivo/token (0600), and export to env.

    Returns the token, or None if user aborted.
    """
    console.print(
        "\n[yellow]The repo appears to be private (or rate-limited).[/yellow] "
        "A GitHub token with [bold]repo[/bold] read access is required."
    )
    console.print("[dim]Get one at https://github.com/settings/tokens (fine-grained or classic)[/dim]")
    token = Prompt.ask("GitHub token (or empty to abort)", password=True, default="").strip()
    if not token:
        return None
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass
    os.environ["GH_TOKEN"] = token
    console.print(f"[dim]Token saved to {TOKEN_FILE} (mode 0600). Future runs will reuse it.[/dim]")
    return token


def _cache_dir(release_tag: str) -> Path:
    return CACHE_BASE / release_tag


def _is_cached(release_tag: str) -> bool:
    d = _cache_dir(release_tag)
    return d.is_dir() and any(d.iterdir())


def _is_auth_error(status: int) -> bool:
    return status in (401, 403, 404)


def _gh_get_json(url: str):
    """GET a GitHub API URL, prompting for a token on auth-like errors and retrying once."""
    for attempt in range(2):
        headers = {**_auth_headers(), "Accept": "application/vnd.github+json"}
        try:
            resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if attempt == 0 and _is_auth_error(status) and _get_token() is None:
                if _prompt_and_save_token() is None:
                    raise RuntimeError(
                        f"GitHub API {status} on {url} and no token provided."
                    ) from e
                continue
            raise RuntimeError(
                f"GitHub API error {status} on {url}: {e.response.text[:200]}"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error on {url}: {e}") from e
    raise RuntimeError(f"Unreachable: exhausted retries for {url}")


SKILLS_TAG_PREFIX = "skills-v"


def _fetch_latest_release_tag() -> str:
    """Return the latest published release tag for the skills bundle.

    The repo has two release tracks (cli-v* and skills-v*), so we cannot rely on
    GitHub's /releases/latest (which may point to a CLI release). Instead, list
    releases in descending publish order and pick the first one tagged skills-v*.
    """
    repo = _repo()
    data = _gh_get_json(f"https://api.github.com/repos/{repo}/releases?per_page=30")
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected releases response shape: {type(data).__name__}")
    for rel in data:
        tag = rel.get("tag_name", "")
        if tag.startswith(SKILLS_TAG_PREFIX) and not rel.get("draft") and not rel.get("prerelease"):
            return tag
    raise RuntimeError(
        f"No published release with tag prefix '{SKILLS_TAG_PREFIX}' found in {repo}."
    )


def _fetch_release_asset_url(release_tag: str) -> str:
    """Return the API asset URL for skills-bundle.tar.gz for the given tag.

    Uses the asset's API `url` (not `browser_download_url`) so private-repo
    downloads work with a Bearer token. The API URL returns a 302 redirect to
    a pre-signed S3 URL; httpx follows it and (correctly) drops the
    Authorization header on the cross-origin hop.
    """
    repo = _repo()
    data = _gh_get_json(f"https://api.github.com/repos/{repo}/releases/tags/{release_tag}")
    for asset in data.get("assets", []):
        if asset["name"] == BUNDLE_ASSET:
            return asset["url"]
    raise RuntimeError(
        f"Asset '{BUNDLE_ASSET}' not found in release {release_tag}. "
        f"Available: {[a['name'] for a in data.get('assets', [])]}"
    )


def _download_and_extract(download_url: str, dest: Path) -> None:
    """Download skills-bundle.tar.gz and extract it into dest."""
    console.print(f"[dim]Downloading {BUNDLE_ASSET}...[/dim]")
    for attempt in range(2):
        headers = {**_auth_headers(), "Accept": "application/octet-stream"}
        try:
            with httpx.stream("GET", download_url, headers=headers, timeout=60, follow_redirects=True) as resp:
                if _is_auth_error(resp.status_code) and attempt == 0 and _get_token() is None:
                    if _prompt_and_save_token() is None:
                        resp.raise_for_status()
                    continue
                resp.raise_for_status()
                with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                    for chunk in resp.iter_bytes(chunk_size=8192):
                        tmp.write(chunk)
                break
        except httpx.RequestError as e:
            raise RuntimeError(f"Download failed: {e}") from e

    dest.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(tmp_path, "r:gz") as tf:
            tf.extractall(dest)
    finally:
        tmp_path.unlink(missing_ok=True)


def ensure_skills_cache(release_tag: Optional[str] = None) -> Path:
    """
    Return the path to a populated skills cache directory.

    1. If QUIVO_LOCAL_SKILLS env is set, return that path directly (offline/dev mode).
    2. Determine release tag (use provided, or fetch latest).
    3. If cache exists for that tag, return it (cache hit).
    4. Otherwise download and extract from GitHub Releases.

    Returns the directory that contains skills/ and manifest.json.
    """
    # Dev/offline override
    local = os.environ.get("QUIVO_LOCAL_SKILLS")
    if local:
        p = Path(local)
        if not p.is_dir():
            raise FileNotFoundError(f"QUIVO_LOCAL_SKILLS={local!r} is not a directory")
        console.print(f"[dim]Using local skills: {p}[/dim]")
        return p

    # Determine tag
    if release_tag is None:
        console.print("[dim]Fetching latest release tag from GitHub...[/dim]")
        release_tag = _fetch_latest_release_tag()
        console.print(f"[dim]Latest release: {release_tag}[/dim]")

    cache = _cache_dir(release_tag)

    if _is_cached(release_tag):
        console.print(f"[dim]Cache hit: {cache}[/dim]")
        return cache

    console.print(f"[dim]Cache miss for {release_tag}, downloading...[/dim]")
    asset_url = _fetch_release_asset_url(release_tag)
    _download_and_extract(asset_url, cache)
    console.print(f"[dim]Extracted to cache: {cache}[/dim]")
    return cache


def list_cached_releases() -> list[str]:
    """Return list of locally cached release tags."""
    if not CACHE_BASE.is_dir():
        return []
    return sorted(
        d.name for d in CACHE_BASE.iterdir() if d.is_dir()
    )


def cache_size_bytes() -> int:
    """Return total size of all cached releases in bytes."""
    if not CACHE_BASE.is_dir():
        return 0
    total = 0
    for p in CACHE_BASE.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total
