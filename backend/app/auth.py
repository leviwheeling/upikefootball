from __future__ import annotations

import hashlib
import hmac
import html
import time
from http import HTTPStatus
from typing import Final
from urllib.parse import parse_qs

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.types import ASGIApp

from app.config import Settings

COOKIE_NAME: Final = "upike_access"
SESSION_SECONDS: Final = 60 * 60 * 2


def _signature(password: str, issued_at: str) -> str:
    payload = f"upike-football:{issued_at}".encode()
    return hmac.new(password.encode(), payload, hashlib.sha256).hexdigest()


def create_session_token(password: str, now: int | None = None) -> str:
    issued_at = str(now if now is not None else int(time.time()))
    return f"{issued_at}.{_signature(password, issued_at)}"


def valid_session_token(
    token: str | None,
    password: str,
    now: int | None = None,
) -> bool:
    if not token:
        return False
    issued_at, separator, supplied_signature = token.partition(".")
    if not separator or not issued_at.isdigit():
        return False
    current_time = now if now is not None else int(time.time())
    age = current_time - int(issued_at)
    if age < 0 or age >= SESSION_SECONDS:
        return False
    return hmac.compare_digest(supplied_signature, _signature(password, issued_at))


def _safe_next(value: str | None) -> str:
    if (
        value
        and value.startswith("/")
        and not value.startswith("//")
        and not any(ord(character) < 32 for character in value)
    ):
        return value
    return "/"


def _login_page(next_path: str, *, error: bool = False, setup_required: bool = False) -> str:
    message = "Incorrect password." if error else ""
    if setup_required:
        message = "Set the Render environment variable named password to enable access."
    disabled = "disabled" if setup_required else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>UPIKE Football - Restricted</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter,ui-sans-serif,system-ui,sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center;
      color: #e8eef7; background: radial-gradient(circle at 75% 0,
      rgba(255,106,50,.14),transparent 34rem),#05080e; }}
    main {{ width: min(420px,calc(100% - 32px)); border: 1px solid rgba(255,255,255,.12);
      border-radius: 12px; background: #090e17; box-shadow: 0 28px 90px rgba(0,0,0,.45); }}
    header {{ display: flex; align-items: center; gap: 12px;
      border-bottom: 1px solid rgba(255,255,255,.1); padding: 18px; }}
    .mark {{ display: grid; width: 42px; height: 42px; place-items: center; border-radius: 7px;
      background: #ff6a32; color: #070a0f; font-weight: 950; }}
    h1 {{ margin: 0; font-size: 15px; letter-spacing: .1em; text-transform: uppercase; }}
    header p {{ margin: 3px 0 0; color: #64748b; font-size: 9px; font-weight: 800;
      letter-spacing: .16em; text-transform: uppercase; }}
    form {{ padding: 24px; }}
    label {{ display: block; margin-bottom: 8px; color: #94a3b8; font-size: 10px;
      font-weight: 850; letter-spacing: .12em; text-transform: uppercase; }}
    input {{ width: 100%; border: 1px solid rgba(255,255,255,.14);
      border-radius: 7px; background: #05080e;
      padding: 13px 14px; color: white; font: inherit; outline: none; }}
    input:focus {{ border-color: #ff6a32; box-shadow: 0 0 0 3px rgba(255,106,50,.1); }}
    button {{ width: 100%; margin-top: 12px; border: 0; border-radius: 7px; background: #ff6a32;
      padding: 13px; color: #070a0f; font-size: 11px; font-weight: 950;
      letter-spacing: .1em; text-transform: uppercase; cursor: pointer; }}
    button:disabled {{ cursor: not-allowed; opacity: .4; }}
    .error {{ margin: 0 0 12px; border: 1px solid rgba(251,113,133,.2); border-radius: 6px;
      background: rgba(251,113,133,.07); padding: 10px; color: #fda4af;
      font-size: 11px; line-height: 1.5; }}
    footer {{ border-top: 1px solid rgba(255,255,255,.08); padding: 13px 18px; color: #475569;
      font-size: 9px; font-weight: 750; letter-spacing: .08em; text-align: center;
      text-transform: uppercase; }}
  </style>
</head>
<body>
  <main>
    <header><div class="mark">UP</div><div><h1>UPIKE Football</h1>
      <p>Restricted analytics</p></div></header>
    <form method="post" action="/login">
      {f'<p class="error">{html.escape(message)}</p>' if message else ""}
      <input type="hidden" name="next" value="{html.escape(next_path, quote=True)}">
      <label for="password">Password</label>
      <input id="password" name="password" type="password" maxlength="256"
        autocomplete="current-password" autofocus required {disabled}>
      <button type="submit" {disabled}>Enter</button>
    </form>
    <footer>Authorized access only</footer>
  </main>
</body>
</html>"""


class PasswordProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        password = self.settings.site_password

        if path == "/api/health":
            return await call_next(request)

        if not password:
            if self.settings.environment == "production":
                return HTMLResponse(
                    _login_page("/", setup_required=True),
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                    headers={"Cache-Control": "no-store"},
                )
            return await call_next(request)

        if path == "/login":
            if request.method == "GET":
                next_path = _safe_next(request.query_params.get("next"))
                return HTMLResponse(_login_page(next_path), headers={"Cache-Control": "no-store"})
            if request.method == "POST":
                body = (await request.body()).decode("utf-8", errors="replace")
                fields = parse_qs(body, keep_blank_values=True)
                supplied = fields.get("password", [""])[0]
                next_path = _safe_next(fields.get("next", ["/"])[0])
                if hmac.compare_digest(supplied, password):
                    response = RedirectResponse(next_path, status_code=HTTPStatus.SEE_OTHER)
                    response.set_cookie(
                        COOKIE_NAME,
                        create_session_token(password),
                        max_age=SESSION_SECONDS,
                        httponly=True,
                        secure=self.settings.environment == "production",
                        samesite="lax",
                        path="/",
                    )
                    response.headers["Cache-Control"] = "no-store"
                    return response
                return HTMLResponse(
                    _login_page(next_path, error=True),
                    status_code=HTTPStatus.UNAUTHORIZED,
                    headers={"Cache-Control": "no-store"},
                )

        if path == "/logout" and request.method == "POST":
            response = RedirectResponse("/login", status_code=HTTPStatus.SEE_OTHER)
            response.delete_cookie(COOKIE_NAME, path="/")
            response.headers["Cache-Control"] = "no-store"
            return response

        if valid_session_token(request.cookies.get(COOKIE_NAME), password):
            return await call_next(request)

        if path.startswith("/api/") or "application/json" in request.headers.get("accept", ""):
            return JSONResponse(
                {"detail": {"code": "authentication_required"}},
                status_code=HTTPStatus.UNAUTHORIZED,
                headers={"Cache-Control": "no-store"},
            )

        next_path = _safe_next(path + (f"?{request.url.query}" if request.url.query else ""))
        return HTMLResponse(
            _login_page(next_path),
            status_code=HTTPStatus.UNAUTHORIZED,
            headers={"Cache-Control": "no-store"},
        )
