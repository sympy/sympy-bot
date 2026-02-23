import os

from aiohttp import web

from .webapp import main_get, main_post, main_health_check

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main_post)
    app.router.add_get("/", main_get)
    app.router.add_get("/health-check", main_health_check)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
