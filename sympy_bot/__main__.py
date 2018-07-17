import os

from aiohttp import web

from .webapp import main_get, main_post

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main_post)
    app.router.add_get("/", main_get)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
