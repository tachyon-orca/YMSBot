# Chatbot for YMSPlays on Twitch

## Dependencies

This bot uses the [TwitchIO](https://github.com/PythonistaGuild/TwitchIO) wrapper for Twitch APIs. Other dependencies are required for data processing, IMDB querying, etc. Install dependencies with:

```
pip install -r requirements.txt
```

## Features

### Basic commands

- `!commands`: list all commands
- `!scoot` to shill Scoot. `!scoot s` (mods only) to start posting every five minutes. `!scoot e` (mods only) to stop. Same for `!gael`.

Commands that only post a blob of text are defined in [`assets/static_commands.json`](assets/static_commands.json).

### Review

Use `!review X` to find YMS's rating/review/watchlist status for movie/TV show X. TV show seasons are not currently supported.

### BRB timer (mods only)

Use `!left` to start BRB timer and `!back` to stop. Use `!brbtime` to check the timer.
