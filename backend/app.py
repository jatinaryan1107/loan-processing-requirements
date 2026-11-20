"""Application composition, lifecycle and the built frontend."""

from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from . import storage
from .routes import router
from .seed import seed_demo

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def create_app(db_path=None, seed=True):
    configured_database = str(db_path or storage.database_path())

    @asynccontextmanager
    async def lifespan(_app):
        token = storage.active_database.set(configured_database)
        try:
            storage.init_db()
            if seed:
                with storage.transaction() as conn:
                    seed_demo(conn)
            yield
        finally:
            storage.active_database.reset(token)

    app = FastAPI(title="Loan Processing Requirements Management", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "If-Match"],
    )

    @app.middleware("http")
    async def headers(request: Request, call_next):
        token = storage.active_database.set(configured_database)
        version_token = storage.expected_version.set(request.headers.get("if-match"))
        try:
            return await handle_request(request, call_next)
        finally:
            storage.expected_version.reset(version_token)
            storage.active_database.reset(token)

    async def handle_request(request: Request, call_next):
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 6 * 1024 * 1024):
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Request exceeds the 6 MB transport limit."}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(router)

    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "API route not found.")
        target = (dist / path).resolve()
        if target.is_relative_to(dist.resolve()) and target.is_file():
            return FileResponse(target)
        if (dist / "index.html").is_file():
            return FileResponse(dist / "index.html")
        raise HTTPException(
            404, "Frontend has not been built. Run npm install and npm run build in frontend/."
        )

    return app


app = create_app()
