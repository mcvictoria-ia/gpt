# Telegram AnythingLLM Bot

This repository contains a minimal Telegram bot that interfaces with AnythingLLM.
The bot supports text, voice and document messages. It can also index images and
allows listing indexed documents as well as closing active claims.

## Setup

1. Install dependencies (and make sure `ffmpeg` is available for audio conversion):

```bash
pip install -r requirements.txt
```

2. Create a `.env` file (or export variables in your environment) with the following variables:

```
TELEGRAM_TOKEN=<your Telegram bot token>
ANYTHINGLLM_API_KEY=<AnythingLLM API key>
ALLOWED_USER_ID=<numeric Telegram user ID allowed to interact>
WORKSPACE_SLUG=<workspace slug>  # optional, defaults to "sabadell"
```

Example `.env` file:

```
TELEGRAM_TOKEN=your-telegram-token
ANYTHINGLLM_API_KEY=your-anythingllm-key
ALLOWED_USER_ID=123456789
WORKSPACE_SLUG=sabadell
```

3. Run the bot:

```bash
python telegram_bot.py
```

The bot will start polling and respond to messages from the allowed user.
Use `/start` to get a welcome message, `/cerrar` to close the current claim and
`/listar` to list indexed documents. You can send voice messages which will be
transcribed automatically and any document or photo you send will be uploaded to
AnythingLLM for indexing.
