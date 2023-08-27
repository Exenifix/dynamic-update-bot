import disnake
from disnake.ext import commands, tasks

from bot import Cog


class SampleCog(Cog):
    @commands.slash_command(name="sample-command")
    async def sample_command(self, inter: disnake.ApplicationCommandInteraction):
        """
        Sample command
        """
        await inter.send("Hi yo mom")

    @tasks.loop(seconds=3, count=3)
    async def sample_loop(self):
        await self.bot.wait_until_ready()
        self.bot.log.info("Sample loop iteration #%d", self.sample_loop.current_loop)
