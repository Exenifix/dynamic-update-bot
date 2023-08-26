import typing as t

from aiohttp import web
from exencolorlogs import Logger

import env

if t.TYPE_CHECKING:
    from bot import Bot


class Application(web.Application):
    bot: "Bot"
    runner: web.AppRunner
    logger: Logger

    def __init__(self, **kwargs):
        super().__init__(logger=Logger("API"), **kwargs)
        self.route = web.RouteTableDef()
        self.on_startup.append(self.startup_callback)
        self.on_cleanup.append(self.cleanup_callback)

    async def run(self, bot: "Bot"):
        self.bot = bot
        self.add_routes(self.route)
        self.runner = web.AppRunner(self)
        await self.runner.setup()
        await web.TCPSite(self.runner, "0.0.0.0", env.env.API_PORT).start()

    async def close(self):
        await self.runner.cleanup()

    async def startup_callback(self, *_):
        self.logger.ok("API started")

    async def cleanup_callback(self, *_):
        self.logger.ok("API closed")


app = Application()


@app.route.post("/update")
async def update(req: web.Request):
    app.logger.debug("Incoming request on /update route from %s", req.remote)
    if req.headers.get("Authorisation", None) != env.env.API_SECRET:
        raise web.HTTPUnauthorized()

    app.bot.reload_extension("sample_extension")
    return web.json_response({"status": "success"})
