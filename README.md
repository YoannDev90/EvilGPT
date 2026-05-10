# EvilGPT 🤖

<!-- Badges -->
<table>
   <tr>
      <td valign="middle" width="120">
         <img src="assets/images/evilgpt.png" alt="EvilGPT Icon" width="120" style="border-radius:8px; display:block; margin:0 auto;">
      </td>
      <td valign="middle">
           <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <a href="https://github.com/YoannDev90/EvilGPT/actions" style="display:inline-block">
            <img src="https://github.com/YoannDev90/EvilGPT/actions/workflows/pre-commit.yml/badge.svg" alt="Lint" style="height:20px; vertical-align:middle;"/>
            </a>
            <a href="https://www.python.org/" style="display:inline-block">
            <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python" style="height:20px; vertical-align:middle;"/>
            </a>
            <a href="LICENSE" style="display:inline-block">
            <img src="https://img.shields.io/badge/license-MIT-green" alt="License" style="height:20px; vertical-align:middle;"/>
            </a>
         </div>
      </td>
   </tr>
</table>

A powerful Discord bot integrating AI models to respond intelligently to user messages in real-time.

## Table of contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Dependencies](#-dependencies)
- [Development](#-development)
- [Adding Providers / Models](#adding-new-providers)
- [License](#-license)

## ✨ Features

- **Discord Integration**: Seamless integration with Discord using discord.py
- **Multi-Model Support**: Support for multiple AI models via LiteLLM
- **Multiple Providers**: Configure different API providers (e.g., Gratisfy) with ease
- **Async Processing**: Non-blocking message processing using asyncio
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Thread-Safe**: Prevents multiple concurrent requests from the same user
- **Dynamic Model Selection**: Automatically selects the best model based on capabilities
- **Persistent Memory**: Conversation history stays in a local CocoIndex-backed SQLite store
- **Transparent Deletion**: Use `/memory list`, `/memory delete`, and `/memory clear` to inspect or purge stored turns

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Discord Bot Token
- API credentials for your chosen AI provider

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YoannDev90/EvilGPT.git
   cd EvilGPT
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Create a `.env` file** in the root directory:
   ```env
   BOT_TOKEN=your_discord_bot_token_here
   GRATISFY_API_BASE=https://api.gratisfy.xyz/v1
   GRATISFY_API_KEY=your_api_key_here
   ```

2. **Configure providers** (optional)
   - Edit `providers.json` to add or modify API providers
   - Edit `models.json` to configure available AI models

3. **Set up your Discord bot**
   - Create a bot on [Discord Developer Portal](https://discord.com/developers/applications)
   - Enable the "Message Content Intent" for the bot to read messages
   - Copy the bot token to your `.env` file

### Running the Bot

```bash
python main.py
```

The bot will start and log in to Discord. You'll see a confirmation message like:
```
Logged in as BotName (ID: 123456789)
```

## 📁 Project Structure
Below is current snapshot of repository. This section is auto-updated by `./lint.sh` on demand.

<!-- TREE-START -->
```
.
├── assets
│   ├── fonts
│   │   ├── NotoSans-BoldItalic.ttf
│   │   ├── NotoSans-Bold.ttf
│   │   ├── NotoSans-Italic.ttf
│   │   └── NotoSans-Regular.ttf
│   └── images
│       ├── evilgpt.png
│       └── evilgpt.svg
├── bot.py
├── cmds
│   ├── __init__.py
│   ├── list_tools.py
│   ├── loader.py
│   ├── memory_clear.py
│   ├── memory_delete.py
│   ├── memory_list.py
│   └── set_mood.py
├── config.toml
├── core
│   ├── config.py
│   ├── model.py
│   ├── models_loader.py
│   └── tools.py
├── data
│   ├── cocoindex_memory.db
│   │   └── mdb
│   │       ├── data.mdb
│   │       └── lock.mdb
│   ├── mcp.json
│   ├── memory.sqlite
│   ├── memory_state.json
│   ├── models.json
│   ├── moods
│   │   ├── aggressive.txt
│   │   ├── jester.txt
│   │   ├── mastermind.txt
│   │   ├── neutral.txt
│   │   ├── nihilist.txt
│   │   └── sarcastic.txt
│   ├── providers.json
│   └── tools
│       ├── run_bash.json
│       ├── run_nodejs.json
│       └── run_python.json
├── .github
│   └── workflows
│       └── pre-commit.yml
├── .gitignore
├── LICENSE
├── lint.sh
├── main.py
├── managers
│   ├── context.py
│   ├── mcp.py
│   ├── memory.py
│   └── tools
│       ├── __init__.py
│       ├── run_bash.py
│       ├── run_nodejs.py
│       └── run_python.py
├── README.md
├── requirements.txt
└── utils
    ├── handlers
    │   ├── codeblock.py
    │   ├── latex.py
    │   ├── messages.py
    │   └── table.py
    ├── logger.py
    └── web_search.py

17 directories, 55 files
```
<!-- TREE-END -->

Run `./lint.sh` to format code and regenerate this project tree snapshot. CI runs the same script on every push/PR.

## 🔧 Technical Details

### AI Model Selection
The bot automatically selects the most appropriate model based on:
- Required input/output formats
- API parameters support
- Model availability

### Message Processing
1. Message received from Discord user
2. Bot checks if user is already processing a request (prevents spam)
3. Message payload is constructed
4. AI model generates response in a thread pool (non-blocking)
5. Response is sent back to Discord

### Supported Features
- Text-to-text AI generation
- Configurable API endpoints
- Fallback model selection
- Token counting and usage tracking
- Performance timing
- Persistent conversation memory with per-turn deletion

## 📦 Dependencies

<!--DEPS-START-->
```markdown
- `discord.py` - A Python wrapper for the Discord API (latest: 2.7.1)
- `python-dotenv` - Read key-value pairs from a .env file and set them as environment variables (latest: 1.2.2)
- `litellm` - Library to easily interface with LLM API providers (latest: 1.83.14)
- `requests` - Python HTTP for Humans. (latest: 2.33.1)
- `colorama` - Cross-platform colored terminal text. (latest: 0.4.6)
- `cairosvg` - A Simple SVG Converter based on Cairo (latest: 2.9.0)
- `Pillow` - Python Imaging Library (fork) (latest: 12.2.0)
- `pilmoji` - Pilmoji is an emoji renderer for Pillow, Python's imaging library. (latest: 2.0.5)
- `microsandbox` - Python SDK for microsandbox — secure, fast microVM-based sandboxing. (latest: 0.4.5)
- `aiohttp` - Async http client/server framework (asyncio) (latest: 3.13.5)
- `discord-webhook` - Easily send Discord webhooks with Python (latest: 1.4.1)
- `cocoindex` - With CocoIndex, users declare the transformation, CocoIndex creates & maintains an index, and keeps the derived index up to date based on source update, with minimal computation and changes. (latest: 1.0.3)
```
<!--DEPS-END-->

## 🛠️ Development

### Linting & CI

- Project provides `lint.sh` at repo root. It runs `ruff format` and `isort .` to format and sort imports.
- Run locally before commit:

```bash
./lint.sh
```

- CI: GitHub Actions workflow runs `lint.sh` on `push` and `pull_request` to `main` and feature branches. Fix issues locally and push again.

If you prefer to install linters manually:

```bash
pip install ruff isort
ruff format
isort .
```

### Adding New Providers
1. Add provider configuration to `providers.json`
2. Set up environment variable for API key
3. Update `config.py` if needed

### Adding New Models
1. Configure the model in `models.json`
2. Ensure the provider has the necessary API credentials

## ⚠️ Important Notes

- The bot ignores messages from other bots and direct messages
- Users cannot send multiple concurrent requests (prevents API overload)
- Message content intent must be enabled for the bot to work
- API keys and tokens should never be committed to version control
- Local memory state lives under `data/memory_state.json` and syncs into a local SQLite store through CocoIndex

## 📝 License

This project is provided as-is. Please respect Discord's Terms of Service and API usage policies.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Made with ❤️ for Discord automation**
