"""OAuth 2.1 implementation — PKCE, token exchange, refresh, discovery.

All token values are stored in the OS keychain via SecretsBackend.
Only metadata (expiry, scopes, URLs) goes to tokens.json.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from crux_cli.paths import tokens_path


def _get_backend():
    """Lazily import and return the secrets backend (avoids import-time sandbox issues)."""
    from crux_cli.secrets import get_backend  # noqa: PLC0415

    return get_backend()


# ---------------------------------------------------------------------------
# PKCE
# ---------------------------------------------------------------------------


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


# ---------------------------------------------------------------------------
# Token metadata storage (not token values — those go in keychain)
# ---------------------------------------------------------------------------


def load_token_metadata() -> dict[str, Any]:
    """Load token metadata from tokens.json."""
    tp = tokens_path()
    if not tp.exists():
        return {}
    try:
        with open(tp) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_token_metadata(metadata: dict[str, Any]) -> None:
    """Save token metadata to tokens.json with restricted permissions."""
    import tempfile

    tp = tokens_path()
    tp.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=tp.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(metadata, f, indent=2, sort_keys=True)
            f.write("\n")
        Path(tmp).replace(tp)
        tp.chmod(0o600)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_auth_server(auth_config: dict[str, Any]) -> tuple[str, str]:
    """Discover authorization and token URLs.

    Fallback chain:
    1. auth.discovery_url
    2. resource_url/.well-known/oauth-protected-resource (RFC 9728)
    3. Explicit auth.authorization_url + auth.token_url
    """
    discovery_url = auth_config.get("discovery_url")
    if discovery_url:
        try:
            data = _fetch_json(discovery_url)
            return data["authorization_endpoint"], data["token_endpoint"]
        except Exception:  # noqa: BLE001, S110
            pass

    resource_url = auth_config.get("resource_url", "")
    if resource_url:
        # Try RFC 9728
        parsed = urllib.parse.urlparse(resource_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for well_known in [
            f"{base}/.well-known/oauth-protected-resource",
            f"{base}/.well-known/oauth-authorization-server",
            f"{base}/.well-known/openid-configuration",
        ]:
            try:
                data = _fetch_json(well_known)
                if "authorization_endpoint" in data and "token_endpoint" in data:
                    return data["authorization_endpoint"], data["token_endpoint"]
            except Exception:  # noqa: BLE001, S112
                continue

    # Explicit URLs
    auth_url = auth_config.get("authorization_url", "")
    token_url = auth_config.get("token_url", "")
    if auth_url and token_url:
        return auth_url, token_url

    msg = "Cannot discover OAuth authorization server — provide authorization_url and token_url"
    raise ValueError(msg)


def _fetch_json(url: str) -> dict[str, Any]:
    """Fetch and parse a JSON document from a URL."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Local redirect server for Authorization Code flow
# ---------------------------------------------------------------------------


class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth redirect."""

    auth_code: str | None = None
    state_received: str | None = None
    error: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        """Handle the OAuth callback redirect."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "error" in params:
            _OAuthCallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authentication failed. You can close this window.")
        elif "code" in params:
            _OAuthCallbackHandler.auth_code = params["code"][0]
            _OAuthCallbackHandler.state_received = params.get("state", [None])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authentication successful! You can close this window.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing authorization code.")

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Suppress default logging."""


def _run_callback_server(timeout: int = 120) -> tuple[str | None, str | None, str | None]:
    """Start a local server, wait for OAuth callback, return (code, state, error)."""
    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.state_received = None
    _OAuthCallbackHandler.error = None

    server = http.server.HTTPServer(("127.0.0.1", 0), _OAuthCallbackHandler)

    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    server.server_close()

    return (
        _OAuthCallbackHandler.auth_code,
        _OAuthCallbackHandler.state_received,
        _OAuthCallbackHandler.error,
    )


# ---------------------------------------------------------------------------
# OAuth flows
# ---------------------------------------------------------------------------


def run_oauth_flow(mcp_name: str, auth_config: dict[str, Any]) -> None:
    """Run OAuth 2.1 Authorization Code + PKCE flow."""
    auth_url, token_url = discover_auth_server(auth_config)
    client_id = auth_config.get("client_id", "crux-cli")
    scopes = auth_config.get("scopes", [])
    resource_url = auth_config.get("resource_url", "")

    verifier, challenge = generate_pkce()
    state = secrets.token_urlsafe(16)

    # Start local server for redirect
    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.state_received = None
    _OAuthCallbackHandler.error = None

    server = http.server.HTTPServer(("127.0.0.1", 0), _OAuthCallbackHandler)
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes) if scopes else "",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    if resource_url:
        params["resource"] = resource_url

    authorize_url = f"{auth_url}?{urllib.parse.urlencode(params)}"

    print("  Opening browser for authentication...")
    opened = webbrowser.open(authorize_url)
    if not opened:
        print(f"\n  Cannot open browser. Open this URL manually:\n  {authorize_url}\n")

    print(f"  Waiting for callback on http://127.0.0.1:{port} (120s timeout)...")

    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    thread.join(timeout=120)
    server.server_close()

    code = _OAuthCallbackHandler.auth_code
    received_state = _OAuthCallbackHandler.state_received
    error = _OAuthCallbackHandler.error

    if error:
        print(f"\u274c OAuth error: {error}")
        sys.exit(1)

    if not code:
        print("\u274c Authentication timed out (120s)")
        sys.exit(1)

    if received_state != state:
        print("\u274c OAuth state mismatch — possible CSRF attack")
        sys.exit(1)

    # Exchange code for tokens
    token_data = _exchange_code(token_url, code, redirect_uri, client_id, verifier, resource_url)

    _store_tokens(mcp_name, token_data, token_url, client_id, scopes)
    print(f"\u2705 OAuth authentication complete for '{mcp_name}'")


def run_client_credentials_flow(mcp_name: str, auth_config: dict[str, Any]) -> None:
    """Run OAuth 2.1 Client Credentials flow (machine-to-machine)."""
    _, token_url = discover_auth_server(auth_config)
    client_id = auth_config.get("client_id", "crux-cli")
    scopes = auth_config.get("scopes", [])
    resource_url = auth_config.get("resource_url", "")

    backend = _get_backend()
    client_secret = backend.get(mcp_name, "client_secret")
    if not client_secret:
        import getpass

        client_secret = getpass.getpass(f"  Enter client_secret for '{mcp_name}': ")
        if not client_secret:
            print("  Skipped — no client_secret entered")
            return
        backend.set(mcp_name, "client_secret", client_secret)

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": " ".join(scopes) if scopes else "",
    }
    if resource_url:
        data["resource"] = resource_url

    try:
        token_data = _post_token_request(token_url, data)
    except Exception as e:  # noqa: BLE001
        print(f"\u274c Token exchange failed: {e}")
        sys.exit(1)

    _store_tokens(mcp_name, token_data, token_url, client_id, scopes)
    print(f"\u2705 Client credentials authentication complete for '{mcp_name}'")


def refresh_access_token(mcp_name: str) -> bool:
    """Refresh an expired OAuth access token using the stored refresh token.

    Returns True if refresh succeeded, False otherwise.
    """
    metadata = load_token_metadata()
    meta = metadata.get(mcp_name)
    if not meta:
        return False

    refresh_account = meta.get("keychain_account_refresh")
    if not refresh_account:
        return False

    backend = _get_backend()
    refresh_token = backend.get(mcp_name, refresh_account)
    if not refresh_token:
        return False

    token_url = meta.get("token_url", "")
    client_id = meta.get("client_id", "crux-cli")
    if not token_url:
        return False

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }

    try:
        token_data = _post_token_request(token_url, data)
    except Exception:  # noqa: BLE001
        return False

    _store_tokens(
        mcp_name,
        token_data,
        token_url,
        client_id,
        meta.get("scopes", []),
    )
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exchange_code(
    token_url: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    code_verifier: str,
    resource_url: str = "",
) -> dict[str, Any]:
    """Exchange authorization code for tokens."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    if resource_url:
        data["resource"] = resource_url

    return _post_token_request(token_url, data)


def _post_token_request(url: str, data: dict[str, str]) -> dict[str, Any]:
    """POST to a token endpoint and return the parsed response."""
    encoded = urllib.parse.urlencode(data).encode("ascii")
    req = urllib.request.Request(  # noqa: S310
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.loads(resp.read())


def _store_tokens(
    mcp_name: str,
    token_data: dict[str, Any],
    token_url: str,
    client_id: str,
    scopes: list[str],
) -> None:
    """Store token values in keychain and metadata in tokens.json."""
    backend = _get_backend()

    access_token = token_data.get("access_token", "")
    if access_token:
        backend.set(mcp_name, "access_token", access_token)

    refresh_token = token_data.get("refresh_token", "")
    if refresh_token:
        backend.set(mcp_name, "refresh_token", refresh_token)

    expires_in = token_data.get("expires_in")
    expires_at = None
    if expires_in:
        from datetime import timedelta

        expires_at = (datetime.now(UTC) + timedelta(seconds=int(expires_in))).isoformat()

    metadata = load_token_metadata()
    metadata[mcp_name] = {
        "auth_type": "oauth",
        "keychain_account_access": "access_token",
        "keychain_account_refresh": "refresh_token" if refresh_token else None,
        "expires_at": expires_at,
        "scopes": scopes,
        "token_url": token_url,
        "client_id": client_id,
    }
    save_token_metadata(metadata)
