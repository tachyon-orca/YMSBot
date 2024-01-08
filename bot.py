import random
import time

import inflect
from twitchio.ext import commands, routines
from dotenv import dotenv_values

from review_utils import ReviewGetter

secrets = dotenv_values(".env")

active_channels = ["imaginaryfanboy"]

inflect_engine = inflect.engine()

scoot_shills = [
    ["Send Scoot money!", 5],
    ["Help Scoot fix his old and broken back!", 1],
    ["Donate to Scoot's MTF (man-to-feline) surgery fund!", 1],
    ["Pussy pics ain't free! Pay Scoot here:", 1],
    ["Happy birthday Scoot! Send him a present!", 1],
    ["Cool Scoot loves you!", 1],
]
scoot_links = " Paypal: paypal.me/notscotthenson If you don't have paypal: https://www.paypal.com/donate/?cmd=_s-xclick&hosted_button_id=NXPSAJ6BF6L72"


def _generate_scoot_shill():
    msgs, weights = zip(*scoot_shills)
    msg = random.choices(msgs, weights=weights)[0]
    return msg + scoot_links


def _format_time_interval(nano_seconds):
    seconds = nano_seconds / 1_000_000_000

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts = []
    for n, v in zip(
        ["day", "hour", "minute", "second"], [days, hours, minutes, seconds]
    ):
        if v:
            v = int(v)
            parts.append(f"{v} {inflect_engine.plural_noun(n, v)}")

    return " ".join(parts)


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
        self.brbtimer = None

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
    @commands.command(name="commands")
    async def list_commands(self, ctx: commands.Context):
        await ctx.send(
            "Commands: !review, !scoot, !brb, !links, !album, !left, !back, !brbtime !feedback"
        )

    @commands.cooldown(rate=1, per=1, bucket=commands.Bucket.channel)
    @commands.command(aliases=("rating", "ratings", "rated"))
    async def review(self, ctx: commands.Context, *args: str):
        title = " ".join(args)
        await ctx.reply(self.review_getter.process_query(title))

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def scoot(self, ctx: commands.Context, arg: str | None):
        if ctx.author.is_mod or ctx.author.is_broadcaster:
            match arg:
                case "s":
                    shill_scoot_recurr.start()
                case "e":
                    shill_scoot_recurr.stop()
                case _:
                    await ctx.send(_generate_scoot_shill())
        else:
            await ctx.send(_generate_scoot_shill())

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def brb(self, ctx: commands.Context):
        await ctx.send(
            "BRB Playlist: https://www.youtube.com/playlist?list=PLRoNIkmOtWKSmvxBBer9WQHnIuwFu1kBe"
        )

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def links(self, ctx: commands.Context):
        await ctx.send(
            "Twitter: twitter.com/2gay2lift. Patreon: patreon.com/YMS. Cameo: cameo.com/Adum. Main channel: youtube.com/@YMS. Gaming channel: youtube.com/@YMSPlays. Highlights: youtube.com/@YMSHighlights. Clips: youtube.com/@YMSClips. Podcast: youtube.com/@Sardonicast. Watch-Alongs: youtube.com/@YMSWatchAlongs. Game VODs: youtube.com/@YMSStreams. YMS Eats: youtube.com/@yourmukbangsucks. Music: youtube.com/@anUnkindness. Scoot's Youtube: youtube.com/@notscotthenson."
        )

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def album(self, ctx: commands.Context):
        await ctx.send(
            "Check out Adum's album on Bandcamp: https://anunkindness.bandcamp.com/album/10-years"
        )

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def left(self, ctx: commands.Context):
        if ctx.author.is_mod or ctx.author.is_broadcaster:
            if self.brbtimer is None:
                self.brbtimer = time.time_ns()
            await ctx.send("peepoLeave Oh no, Adum has left the stream!")

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def back(self, ctx: commands.Context):
        if ctx.author.is_mod or ctx.author.is_broadcaster:
            msg = "peepoArrive Adum is back!"
            if self.brbtimer is not None:
                brbtime = time.time_ns() - self.brbtimer
                self.brbtimer = None
                msg += f" He was gone for {_format_time_interval(brbtime)}."
            await ctx.send(msg)

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def brbtime(self, ctx: commands.Context):
        if self.brbtimer is not None:
            brbtime = time.time_ns() - self.brbtimer
            await ctx.send(f"Adum has been gone for {_format_time_interval(brbtime)}.")

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def feedback(self, ctx: commands.Context):
        await ctx.send(
            "This bot is maintained by @tachyon_orca. You can find its code on GitHub: https://github.com/tachyon-orca/YMSBot. Feel free to open an issue or pull request if you have any suggestions or feedback!"
        )


bot = Bot()
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
