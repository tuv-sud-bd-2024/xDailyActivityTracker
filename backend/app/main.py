from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from .db import init_db
from .routes import parse as parse_routes
from .routes import ui as ui_routes
from .routes import auth as auth_routes
from .routes import admin as admin_routes
from .auth import create_initial_admin, get_user_from_token_optional
from .config import settings
import base64
from starlette.responses import Response

app = FastAPI(title="xDailyActivityTracker Backend")

templates = Jinja2Templates(directory="backend/app/templates")


@app.on_event("startup")
def on_startup():
    init_db()
    create_initial_admin()


app.include_router(parse_routes.router, prefix="/api/parse")
app.include_router(auth_routes.router, prefix="/api/auth")
app.include_router(admin_routes.router, prefix="/admin")
app.include_router(ui_routes.router, prefix="/ui")
from .routes import activities as activities_routes
app.include_router(activities_routes.router, prefix="/api")


@app.get("/")
def index(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/api/auth/login", status_code=302)
    user = get_user_from_token_optional(token)
    if not user:
        return RedirectResponse(url="/api/auth/login", status_code=302)
    return templates.TemplateResponse("parse_paste.html", {"request": request})


@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    """Simple HTTP Basic auth wrapper protecting all routes.
    Credentials are taken from env vars `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD`.
    """
    # Allow internal health check or localhost? We'll require auth for all requests.
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return Response(status_code=401, headers={"WWW-Authenticate": "Basic realm=\"xDailyActivityTracker\""})
    try:
        scheme, _, credentials = auth_header.partition(" ")
        if scheme.lower() != "basic":
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic realm=\"xDailyActivityTracker\""})
        decoded = base64.b64decode(credentials).decode("utf-8")
        username, _, password = decoded.partition(":")
        if username != settings.BASIC_AUTH_USERNAME or password != settings.BASIC_AUTH_PASSWORD:
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic realm=\"xDailyActivityTracker\""})
    except Exception:
        return Response(status_code=401, headers={"WWW-Authenticate": "Basic realm=\"xDailyActivityTracker\""})
    # passed basic auth
    response = await call_next(request)
    return response
