# Chatbot for YMSPlays on Twitch

## Dependencies

Use Python 3.15. This bot uses the [TwitchIO](https://github.com/TwitchIO/TwitchIO) wrapper for Twitch APIs. Other dependencies are required for data processing and IMDb querying. Install the pinned, hashed dependencies with:

```
python -m pip install --only-binary=:all: --require-hashes -r requirements.txt
```

The Dockerfile pins Python 3.15.1 on Debian trixie by image digest. It applies
available Debian updates at build time. Rebuild with `--pull --no-cache` to pick
up OS fixes, and update the base tag and digest when a new Python release ships.

Edit `requirements.in` for bot dependencies and `requirements-maintenance.in`
for the asset update job. Regenerate both locks with Python 3.15 in a separate
virtual environment:

```sh
python3.15 -m venv /tmp/ymsbot-dependency-tools
/tmp/ymsbot-dependency-tools/bin/pip install pip-tools==7.6.2 pip-audit==2.10.1
/tmp/ymsbot-dependency-tools/bin/pip-compile --upgrade --generate-hashes --strip-extras --pip-args='--only-binary=:all:' requirements.in
/tmp/ymsbot-dependency-tools/bin/pip-compile --upgrade --generate-hashes --strip-extras --pip-args='--only-binary=:all:' requirements-maintenance.in
/tmp/ymsbot-dependency-tools/bin/pip-audit --disable-pip --no-deps -r requirements.txt
/tmp/ymsbot-dependency-tools/bin/pip-audit --disable-pip --no-deps -r requirements-maintenance.txt
docker build --pull --no-cache -t ymsbot-test .
docker run --rm --network none -v "$PWD:/app:ro" ymsbot-test python -m unittest discover -s tests -v
```

Tests use dummy credentials, make no network requests, and leave tokens and
assets untouched. They exercise Twitch command registration, the Starlette
adapter, dependency imports, review formatting, and the IMDb fallback.
IMDb search uses `requests` and `lxml`; PyMovieDb's browser dependency chain is
no longer needed, allowing a supported urllib3 release and verified TLS.

The dependency audit workflow runs on pull requests, relevant pushes, and weekly.
Dependabot proposes Python, Docker, and GitHub Actions updates. The self-hosted
asset update runner needs Actions Runner 2.327.1 or later for the updated actions.
The separate `tachyorca/imdb_user_crawler:main` image used by that job has its own
dependencies and is outside the bot image's dependency lock and Python audit.

## Features

### Basic commands

- `!commands`: list all commands

Commands that only post a blob of text are defined in [`assets/static_commands.json`](assets/static_commands.json).

### Review

Use `!review X` to find YMS's rating/review/watchlist status for movie/TV show X. TV show seasons are not currently supported.

### BRB timer (mods only)

Use `!left` to start BRB timer and `!back` to stop. Use `!brbtime` to check the timer.
