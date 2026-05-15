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
<!--ENV-START-->
```env
BOT_TOKEN=
WEBHOOK_URL=
ELECTRONHUB_API_KEY=
MEGANOVA_API_KEY=
MISTRAL_API_KEY=
MNN_API_KEY=
NAVY_API_KEY=
PAXSENIX_API_KEY=
ZANITY_API_KEY=
EVOLVEX_API_KEY=
AQUA_API_KEY=
NVIDIA_NIM_API_KEY=
```
<!--ENV-END-->


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
│   ├── health.py
│   ├── __init__.py
│   ├── list_tools.py
│   ├── loader.py
│   ├── memory_clear.py
│   ├── memory_delete.py
│   ├── memory_list.py
│   ├── ping.py
│   ├── set_mood.py
│   └── _shared.py
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
│   ├── command_sync_state.json
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
│       ├── image_ocr.json
│       ├── run_bash.json
│       ├── run_nodejs.json
│       ├── run_python.json
│       ├── safe_eval_math.json
│       ├── sandbox_create.json
│       ├── sandbox_exec.json
│       ├── sandbox_fs_list.json
│       ├── sandbox_fs_mkdir.json
│       ├── sandbox_fs_read.json
│       ├── sandbox_fs_remove.json
│       ├── sandbox_fs_stat.json
│       ├── sandbox_fs_write.json
│       ├── sandbox_inspect.json
│       ├── sandbox_list.json
│       ├── sandbox_metrics.json
│       ├── sandbox_remove.json
│       ├── sandbox_run.json
│       ├── sandbox_shell.json
│       └── sandbox_stop.json
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
│       ├── image_ocr.py
│       ├── __init__.py
│       ├── run_bash.py
│       ├── run_nodejs.py
│       ├── run_python.py
│       ├── safe_eval_math.py
│       ├── sandbox_create.py
│       ├── sandbox_exec.py
│       ├── sandbox_fs_list.py
│       ├── sandbox_fs_mkdir.py
│       ├── sandbox_fs_read.py
│       ├── sandbox_fs_remove.py
│       ├── sandbox_fs_stat.py
│       ├── sandbox_fs_write.py
│       ├── sandbox_inspect.py
│       ├── sandbox_list.py
│       ├── sandbox_metrics.py
│       ├── sandbox_remove.py
│       ├── sandbox_run.py
│       ├── sandbox_shell.py
│       └── sandbox_stop.py
├── README.md
├── requirements.txt
└── utils
    ├── handlers
    │   ├── codeblock.py
    │   ├── latex.py
    │   ├── messages.py
    │   └── table.py
    └── logger.py

17 directories, 92 files
```
<!-- TREE-END -->

<!-- CODE-STATS-START -->
## Code Statistics

**Shell:** 1 files, 167 lines of code

**JSON:** 25 files, 402 lines of code

**Markdown:** 1 files, 279 lines of code

**Python:** 45 files, 3674 lines of code

**SVG:** 1 files, 17 lines of code

**TOML:** 1 files, 13 lines of code

**Text:** 7 files, 177 lines of code

**Total:** 81 files, 4729 lines of code, 1938 comments, 1155 blank lines
<!-- CODE-STATS-END -->

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
- `discord.py==2.7.1` - A Python wrapper for the Discord API (latest: 2.7.1)
- `python-dotenv==1.2.2` - Read key-value pairs from a .env file and set them as environment variables (latest: 1.2.2)
- `litellm==1.84.0` - Library to easily interface with LLM API providers (latest: 1.84.0)
- `requests==2.34.2` - Python HTTP for Humans. (latest: 2.34.2)
- `colorama==0.4.6` - Cross-platform colored terminal text. (latest: 0.4.6)
- `cairosvg==2.9.0` - A Simple SVG Converter based on Cairo (latest: 2.9.0)
- `Pillow==12.2.0` - Python Imaging Library (fork) (latest: 12.2.0)
- `pilmoji==2.0.5` - Pilmoji is an emoji renderer for Pillow, Python's imaging library. (latest: 2.0.5)
- `microsandbox==0.4.6` - Python SDK for microsandbox — secure, fast microVM-based sandboxing. (latest: 0.4.6)
- `aiohttp==3.13.5` - Async http client/server framework (asyncio) (latest: 3.13.5)
- `discord-webhook==1.4.1` - Easily send Discord webhooks with Python (latest: 1.4.1)
- `cocoindex==1.0.5` - With CocoIndex, users declare the transformation, CocoIndex creates & maintains an index, and keeps the derived index up to date based on source update, with minimal computation and changes. (latest: 1.0.5)
- `fastmcp==3.3.0` - The fast, Pythonic way to build MCP servers and clients. (latest: 3.3.1)
- `pytesseract==0.3.13` - Python-tesseract is a python wrapper for Google's Tesseract-OCR (latest: 0.3.13)
- `pint==0.25.3` - Physical quantities module (latest: 0.25.3)
```
<!--DEPS-END-->

## 🛠️ Development

### Linting & CI

- Project provides `lint.sh` at repo root. 
- Run locally before commit:

```bash
./lint.sh
```

- CI: GitHub Actions workflow runs `lint.sh` on `push` and `pull_request` to `master` and feature branches. Fix issues locally and push again.

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
