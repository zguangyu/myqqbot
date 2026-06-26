# QQ Bot Agent

## Quick Start

```bash
# Run locally
cp .env.example .env  # Fill in credentials
python main.py

# Docker
docker build -t qqbot .
docker run --env-file .env qqbot
```

## Architecture

Two files only:
- `main.py` - QQ bot client, event handlers, slash commands (`/help`, `/model`)
- `chat_agent.py` - LangGraph agent with memory and context compression

## Environment Variables

`MODEL_NAME` is **comma-separated list** (not single model). Example: `gpt-4o-mini,claude-3-haiku`

Required: `QQ_APPID`, `QQ_SECRET`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`

## Conventions

- **Language:** All code comments, user-facing strings, and documentation are in **Chinese**
- **No tests or CI:** Run `python main.py` to verify changes manually
- **No linter/formatter:** Follow existing code style

## Key Patterns

- Thread ID format: `guild_{channel_id}`, `dms_{channel_id}`, `c2c_{user_openid}`, `group_{group_openid}`
- State is in-memory only (`MemorySaver`) - lost on restart
- Context compression triggers when messages exceed `COMPRESS_THRESHOLD` (default 15)
- System prompt injected per thread on first message; instructs bot to reply short and plain-text (no Markdown)
