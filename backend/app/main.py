"""Lumina backend entrypoint.

Runs a local FastAPI service bound to the loopback interface. When started by
the Electron shell with LUMINA_PORT=0, the OS assigns a free port and the
actual bound port is printed to stdout as `LUMINA_PORT=<n>` so the launcher can
discover it.
"""
from __future__ import annotations

import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1 import bible, projects, system, templates
from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.core.responses import err


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.ensure_dirs()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=__version__, lifespan=lifespan)

    # Local desktop app: renderer runs on a different origin (file:// or vite
    # dev server), so allow all — the server only binds to loopback anyway.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=err(exc.code.value, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=err(ErrorCode.VALIDATION_ERROR.value, "请求参数校验失败", exc.errors()),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=err(ErrorCode.INTERNAL_ERROR.value, "服务器内部错误", str(exc)),
        )

    api_prefix = "/api/v1"
    app.include_router(system.router, prefix=api_prefix)
    app.include_router(bible.router, prefix=api_prefix)
    app.include_router(projects.router, prefix=api_prefix)
    app.include_router(templates.router, prefix=api_prefix)

    return app


app = create_app()


def _pick_port(host: str, port: int) -> int:
    """Resolve a concrete port (when configured port is 0, bind to find one)."""
    if port != 0:
        return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def main() -> None:
    import uvicorn

    host = settings.host
    port = _pick_port(host, settings.port)
    # Contract with the Electron launcher: announce the bound port on stdout.
    print(f"LUMINA_PORT={port}", flush=True)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
