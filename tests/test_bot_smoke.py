import asyncio
import importlib
import unittest
from unittest.mock import Mock, patch

with patch("dotenv.dotenv_values", return_value={"TMDB_READ_ACCESS_TOKEN": "test"}):
    import bot
    from review_utils import ReviewGetter


class DependencySmokeTests(unittest.TestCase):
    def test_dependency_imports(self):
        for name in ("aiohttp", "discord", "fire", "git", "inflect", "lxml.html",
                     "numpy", "pandas", "requests", "starlette", "tqdm", "twitchio", "uvicorn"):
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_timer_formatting(self):
        self.assertEqual(bot._format_time_interval(90061 * 1_000_000_000),
                         "1 day 1 hour 1 minute 1 second")

    def test_real_assets_load_and_direct_id_formats(self):
        reviews = ReviewGetter()
        reviews._refresh_assets = Mock()
        imdb_id = next(key for key, value in reviews.ratings.items()
                       if key not in ("tt4686132", "tt0072725") and value.get("title"))
        reply = reviews.process_query(imdb_id, embed_title_link=True)
        self.assertIn("Adum gave", reply)
        self.assertIn(f"https://www.imdb.com/title/{imdb_id}/", reply)
        self.assertIn("/10", reply)


class TwitchSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = bot.Bot(client_id="test", client_secret="test", bot_id="1",
                              owner_id="2", prefix="!")

    async def asyncTearDown(self):
        # No authentication, token reads/writes, or Twitch connections in tests.
        await self.client.close(save_tokens=False)

    async def test_static_and_dynamic_commands_register(self):
        await self.client.add_component(bot.DynamicCommands())
        for command in ("commands", "review", "left", "back", "brbtime"):
            self.assertIsNotNone(self.client.get_command(command), command)
        self.assertIs(self.client.get_command("rating"), self.client.get_command("review"))
        self.assertTrue(self.client.static_commands)
        for command in self.client.static_commands:
            self.assertIsNotNone(self.client.get_command(command), command)

    async def test_starlette_adapter_serves_without_authentication(self):
        # Call the real ASGI adapter to exercise its Starlette middleware stack.
        messages = []
        events = asyncio.Queue()
        events.put_nowait({"type": "http.request", "body": b"", "more_body": False})

        async def send(message):
            messages.append(message)

        await self.client._adapter(
            {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
             "method": "GET", "scheme": "http", "path": "/missing",
             "raw_path": b"/missing", "query_string": b"", "root_path": "",
             "headers": [], "server": ("test", 4343), "client": ("test", 12345)},
            events.get, send,
        )
        self.assertEqual(messages[0]["status"], 404)


if __name__ == "__main__":
    unittest.main()
