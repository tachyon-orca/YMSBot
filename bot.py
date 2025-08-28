import asyncio
import json
import logging
import time
from datetime import datetime, timezone

import inflect
import twitchio
from dotenv import dotenv_values
from review_utils import ReviewGetter
from twitchio import authentication, eventsub, web
from twitchio.ext import commands

LOGGER: logging.Logger = logging.getLogger(__name__)

inflect_engine = inflect.engine()


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
    def __init__(self, **kwargs) -> None:
        adapter = web.StarletteAdapter(domain="bot.tachyorca.com", port=4343)
        super().__init__(adapter=adapter, **kwargs)
        self.load_static_commands()

    async def setup_hook(self) -> None:
        # Add our General Commands Component...
        await self.add_component(DynamicCommands())

        with open(".tio.tokens.json", "rb") as fp:
            tokens = json.load(fp)

        for user_id in tokens:
            if user_id == self.bot_id:
                continue

            # Subscribe to chat for everyone we have a token...
            chat = eventsub.ChatMessageSubscription(
                broadcaster_user_id=user_id, user_id=self.bot_id
            )
            await self.subscribe_websocket(chat)

    async def event_ready(self) -> None:
        LOGGER.info("Logged in as: %s", self.user)

    async def event_oauth_authorized(
        self, payload: authentication.UserTokenPayload
    ) -> None:
        # Stores tokens in .tio.tokens.json by default; can be overriden to use a DB for example
        # Adds the token to our Client to make requests and subscribe to EventSub...
        await self.add_token(payload.access_token, payload.refresh_token)

        if payload.user_id == self.bot_id:
            return

        # Subscribe to chat for new authorizations...
        chat = eventsub.ChatMessageSubscription(
            broadcaster_user_id=payload.user_id, user_id=self.bot_id
        )
        await self.subscribe_websocket(chat)

    def load_static_commands(self, commands_file="assets/static_commands.json"):
        self.static_commands = []
        with open(commands_file) as f:
            static_commands = json.load(f)
        for cmd in static_commands:

            def _make_command(cmd):
                @commands.cooldown(rate=1, per=5, key=commands.BucketType.channel)
                async def _cmd(ctx: commands.Context):
                    await ctx.send(cmd["message"])

                return _cmd

            packaged = commands.Command(
                name=cmd["name"], aliases=cmd["aliases"], callback=_make_command(cmd)
            )
            self.add_command(packaged)
            hidden = cmd.get("hidden", False)
            if not hidden:
                self.static_commands.append(cmd["name"])

    @commands.command(name="commands")
    @commands.cooldown(rate=1, per=5, key=commands.BucketType.channel)
    async def list_commands(self, ctx: commands.Context):
        await ctx.send(
            ", ".join(
                ["Commands: !review, !left, !back, !brbtime"]
                + [f"!{cmd}" for cmd in self.static_commands]
            )
            + ". All commands have a 5 second cooldown."
        )


class DynamicCommands(commands.Component):
    def __init__(self):
        self.review_getter = ReviewGetter()
        self.brbtimer = None

    @commands.cooldown(rate=1, per=5, key=commands.BucketType.user)
    @commands.command(aliases=("rating", "ratings", "rated"))
    async def review(self, ctx: commands.Context, *args: str):
        title = " ".join(args)
        await ctx.reply(self.review_getter.process_query(title))

    @commands.cooldown(rate=1, per=5, key=commands.BucketType.channel)
    @commands.command()
    async def left(self, ctx: commands.Context):
        if ctx.author.moderator or ctx.author.broadcaster:
            if self.brbtimer is None:
                self.brbtimer = time.time_ns()
            await ctx.send("peepoLeave Oh no, Adum has left the stream!")

    @commands.cooldown(rate=1, per=5, key=commands.BucketType.channel)
    @commands.command()
    async def back(self, ctx: commands.Context):
        if ctx.author.moderator or ctx.author.broadcaster:
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

    @commands.cooldown(rate=1, per=5, key=commands.BucketType.channel)
    @commands.command()
    async def brbtime(self, ctx: commands.Context):
        if self.brbtimer is not None:
            brbtime = time.time_ns() - self.brbtimer
            await ctx.send(f"Adum has been gone for {_format_time_interval(brbtime)}.")


def main() -> None:
    secrets = dotenv_values(".env")
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with Bot(
            client_id=secrets["CLIENT_ID"],
            client_secret=secrets["CLIENT_SECRET"],
            bot_id=secrets["BOT_ID"],
            owner_id=secrets["OWNER_ID"],
            prefix="!",
        ) as bot:
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt")


if __name__ == "__main__":
    main()
