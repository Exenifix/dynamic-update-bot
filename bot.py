import importlib.machinery
import importlib.util
import inspect
import sys

import disnake
from disnake.ext import commands, tasks
from exencolorlogs import Logger

import env
from api import app


class Bot(commands.InteractionBot):
    def __init__(self):
        super().__init__(intents=disnake.Intents.default())
        self.log = Logger()

    def run(self) -> None:
        self.log.info("Loading extension...")
        self.load_extension("sample_extension")
        self.log.ok("Extension loaded")
        self.log.info("Connecting...")
        super().run(env.env.TOKEN)

    async def start(self, *args, **kwargs) -> None:
        await app.run(self)
        await super().start(*args, **kwargs)

    async def close(self) -> None:
        await app.close()
        await super().close()

    async def on_ready(self):
        self.log.ok("Bot is ready!")

    def _load_from_module_spec(
        self, spec: importlib.machinery.ModuleSpec, key: str
    ) -> None:
        # this is copied from source and overwritten a bit
        lib = importlib.util.module_from_spec(spec)
        self.log.debug("Loading extension %s", lib.__name__)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            del sys.modules[key]
            raise commands.ExtensionFailed(key, e) from e

        try:
            setup = lib.setup
        except AttributeError:

            def setup(bot: Bot):
                for _, cog in inspect.getmembers(
                    lib,
                    lambda x: inspect.isclass(x)
                    and issubclass(x, commands.Cog)
                    and x is not Cog,
                ):
                    bot.log.debug("Adding cog %s", cog.__name__)
                    bot.add_cog(cog(bot))
                    bot.log.debug("Cog %s added", cog.__name__)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise commands.ExtensionFailed(key, e) from e
        else:
            self._CommonBotBase__extensions[key] = lib  # type: ignore
            self.log.debug("Extension %s loaded successfully", lib.__name__)


class Cog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        loop: tasks.Loop
        for _, loop in inspect.getmembers(self, lambda x: isinstance(x, tasks.Loop)):
            self.bot.log.debug(
                "Starting %s.%s loop", self.__class__.__name__, loop.coro.__name__
            )
            loop.start()
