import discord
from discord.ext import commands
from dotenv import dotenv_values

from review_utils import ReviewGetter

secrets = dotenv_values(".env")
token = secrets["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
review_getter = ReviewGetter()


@bot.command()
async def review(ctx, *args: str):
    title = " ".join(args)
    await ctx.send(review_getter.process_query(title, embed_title_link=True))


bot.run(token)
