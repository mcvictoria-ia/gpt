# Telegram AnythingLLM Bot

This repository contains a minimal Telegram bot that interfaces with AnythingLLM. The bot supports text, voice and document messages. It also allows listing indexed documents and closing active claims.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables (they will be loaded automatically at runtime):

```
TELEGRAM_TOKEN=<your Telegram bot token>
ANYTHINGLLM_API_KEY=<AnythingLLM API key>
ALLOWED_USER_ID=<numeric Telegram user ID allowed to interact>
WORKSPACE_SLUG=<workspace slug>  # optional, defaults to "sabadell"
```

3. Run the bot:

```bash
python telegram_bot.py
```

The bot will start polling and respond to messages from the allowed user.
