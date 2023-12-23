import random

from twitchio.ext import commands, routines
from dotenv import dotenv_values

from review_utils import ReviewGetter

secrets = dotenv_values(".env")

active_channels = ["tachyon_orca"]

scoot_shills = [
    ["Send Scoot money!", 5],
    ["Help Scoot fix his old and broken back!", 1],
    ["Donate to Scoot's MTF (man-to-feline) surgery fund!", 1],
    ["Pussy pics ain't free! Pay Scoot here.", 1],
    ["Happy birthday Scoot! Send him a present!", 1],
]
scoot_links = " Paypal: paypal.me/notscotthenson If you don't have paypal: https://www.paypal.com/donate/?cmd=_s-xclick&hosted_button_id=NXPSAJ6BF6L72"


def _generate_scoot_shill():
    msgs, weights = zip(*scoot_shills)
    msg = random.choices(msgs, weights=weights)[0]
    return msg + scoot_links


@routines.routine(minutes=5)
async def shill_scoot_recurr():
    for chname in active_channels:
        channel = bot.get_channel(chname)
        await channel.send(_generate_scoot_shill())


class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(
            token=secrets["ACCESS_TOKEN"], prefix="!", initial_channels=active_channels
        )
        self.review_getter = ReviewGetter()

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        if message.channel.name not in active_channels:
            print(f"Bot in wrong channel: {message.channel.name}")
            return
        # print(message.content)

        await self.handle_commands(message)

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def review(self, ctx: commands.Context, *args: str):
        title = " ".join(args)
        await ctx.reply(self.review_getter.process_query(title))

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def scoot(self, ctx: commands.Context, arg: str | None):
        match arg:
            case "s":
                shill_scoot_recurr.start()
            case "e":
                shill_scoot_recurr.stop()
            case _:
                await ctx.send(_generate_scoot_shill())


bot = Bot()
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
