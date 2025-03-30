import json
import random
import time
from datetime import datetime, timezone

import inflect
from dotenv import dotenv_values
from twitchio.ext import commands, routines

from review_utils import ReviewGetter

secrets = dotenv_values(".env")

active_channels = ["ymsplays"]

inflect_engine = inflect.engine()

# scoot_shills = [
#     ["Please support Scoot!", 5],
#     ["Send Scoot money!", 1],
#     ["Help Scoot fix his old and broken back!", 1],
#     ["Donate to Scoot's MTF (man-to-feline) surgery fund!", 1],
#     ["Pussy pics ain't free! Pay Scoot here:", 1],
#     ["Happy birthday Scoot! Send him a present!", 1],
#     ["Cool Scoot loves you!", 1],
#     ["UwU what's this? Is it fow Scoot?", 0.1],
# ]
# scoot_links = " Paypal: paypal.me/notscotthenson If you don't have paypal: https://www.paypal.com/donate/?cmd=_s-xclick&hosted_button_id=NXPSAJ6BF6L72 Cameo: https://www.cameo.com/scoot Wrestling merch: prowrestlingtees.com/scotthenson Youtube: youtube.com/@notscotthenson Discord: discord.gg/zXXv7p92xr"


# gael_msg = "Gaël's Paypal: https://www.paypal.com/paypalme/vexelg Twitter: https://twitter.com/_vexel"

# def _generate_scoot_shill():
#     msgs, weights = zip(*scoot_shills)
#     msg = random.choices(msgs, weights=weights)[0]
#     return msg + scoot_links

# @routines.routine(minutes=10)
# async def shill_scoot_recurr():
#     for chname in active_channels:
#         channel = bot.get_channel(chname)
#         await channel.send(_generate_scoot_shill())


# @routines.routine(minutes=10)
# async def shill_gael_recurr():
#     for chname in active_channels:
#         channel = bot.get_channel(chname)
#         await channel.send(gael_msg)


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
        self.load_static_commands()

    def load_static_commands(self):
        self.static_commands = []
        with open("assets/static_commands.json") as f:
            static_commands = json.load(f)
        for cmd in static_commands:

            def _make_command(cmd):
                async def _cmd(ctx: commands.Context):
                    await ctx.send(cmd["message"])

                return _cmd

            commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)(
                self.command(
                    name=cmd["name"],
                    aliases=cmd["aliases"] if len(cmd["aliases"]) > 0 else None,
                )(_make_command(cmd))
            )
            hidden = cmd.get("hidden", False)
            if not hidden:
                self.static_commands.append(cmd["name"])

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
            ", ".join(
                ["Commands: !review, !scoot, !gael, !left, !back, !brbtime"]
                + [f"!{cmd}" for cmd in self.static_commands]
            )
            + ". All commands have a 5 second cooldown."
        )

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.user)
    @commands.command(aliases=("rating", "ratings", "rated"))
    async def review(self, ctx: commands.Context, *args: str):
        title = " ".join(args)
        await ctx.reply(self.review_getter.process_query(title))

    # @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    # @commands.command()
    # async def scoot(self, ctx: commands.Context, arg: str | None):
    #     if ctx.author.is_mod or ctx.author.is_broadcaster:
    #         match arg:
    #             case "s":
    #                 shill_scoot_recurr.start()
    #             case "e":
    #                 shill_scoot_recurr.stop()
    #             case _:
    #                 await ctx.send(_generate_scoot_shill())
    #     else:
    #         await ctx.send(_generate_scoot_shill())

    # @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    # @commands.command()
    # async def gael(self, ctx: commands.Context, arg: str | None):
    #     if ctx.author.is_mod or ctx.author.is_broadcaster:
    #         match arg:
    #             case "s":
    #                 shill_gael_recurr.start()
    #             case "e":
    #                 shill_gael_recurr.stop()
    #             case _:
    #                 await ctx.send(gael_msg)
    #     else:
    #         await ctx.send(gael_msg)

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
                msg += f" He was gone for {_format_time_interval(brbtime)}."
                with open("brb_log.jsonl", "a") as f:
                    f.write(
                        json.dumps(
                            {
                                "channel": ctx.channel.name,
                                "brb_start": datetime.fromtimestamp(
                                    self.brbtimer / 1e9, tz=timezone.utc
                                ).strftime(r"%Y-%m-%d %H:%M:%S %Z"),
                                "brb_time": str(brbtime / 1e9),
                            }
                        )
                        + "\n"
                    )
                self.brbtimer = None
            await ctx.send(msg)

    @commands.cooldown(rate=1, per=5, bucket=commands.Bucket.channel)
    @commands.command()
    async def brbtime(self, ctx: commands.Context):
        if self.brbtimer is not None:
            brbtime = time.time_ns() - self.brbtimer
            await ctx.send(f"Adum has been gone for {_format_time_interval(brbtime)}.")


bot = Bot()
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
