import os, random, string
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.routing import Route
from datetime import datetime
from deta import Base

db = Base("links")


async def home(request):
    return HTMLResponse("Hello, world!")


async def add(request):
    payload = await request.json()

    # skip the junk
    if not payload or "url" not in payload:
        return JSONResponse({"message": "No url provided"}, 400)
    if not payload["url"].startswith("http"):
        return JSONResponse({"message": "Invalid url"}, 400)
    if "slug" in payload and payload["slug"] == "api":
        return JSONResponse({"message": "Invalid slug"}, 400)

    # TODO: handle when random slug already exists
    try:
        item = db.insert(
            {
                "url": payload["url"],
                "hits": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "key": payload.get(
                    "slug",
                    "".join(
                        random.choices(string.ascii_lowercase + string.digits, k=6)
                    ),
                ),
            }
        )
    except Exception as e:
        if e.code == 409:
            return JSONResponse({"message": "Slug already exists"}, 400)
        return JSONResponse({"message": "Something went wrong"}, 500)

    return JSONResponse(item)


async def redirect(request):
    slug = request.path_params["slug"]
    item = db.get(slug)
    if not item:
        return HTMLResponse("lonk not found, friendo", 404)
    db.update({"hits": db.util.increment()}, slug)
    return RedirectResponse(item["url"])


app = Starlette(
    debug=os.getenv("DETA_RUNTIME", True),
    routes=[
        Route("/", home, methods=["GET"]),
        Route("/api/add", add, methods=["POST"]),
        Route("/{slug}", redirect, methods=["GET"]),
    ],
)
