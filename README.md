# EvilGPT 🤖

A powerful Discord bot that integrates AI models to respond intelligently to user messages in real-time.

## ✨ Features

- **Discord Integration**: Seamless integration with Discord using discord.py
- **Multi-Model Support**: Support for multiple AI models via LiteLLM
- **Multiple Providers**: Configure different API providers (e.g., Gratisfy) with ease
- **Async Processing**: Non-blocking message processing using asyncio
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Thread-Safe**: Prevents multiple concurrent requests from the same user
- **Dynamic Model Selection**: Automatically selects the best model based on capabilities

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

```
EvilGPT/
├── main.py                 # Entry point and logging setup
├── bot.py                  # Discord bot implementation
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── providers.json          # API provider configurations
├── models.json             # Available AI models
├── ai_utils/
│   ├── __init__.py
│   ├── ai_model.py         # AI model selection and response generation
│   └── get_models.py       # Model and provider loading
└── discord_utils/
    ├── __init__.py
    ├── get_emojis.py       # Emoji utilities
    └── get_members.py      # Member utilities
```

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

## 📦 Dependencies

- `discord.py>=2.3` - Discord API wrapper
- `litellm>=1.0` - LLM provider abstraction
- `python-dotenv>=1.0` - Environment variable management
- `requests>=2.31` - HTTP requests library

## 🛠️ Development

### Logging
The bot uses Python's standard logging module. Adjust the log level in `main.py`:
```python
setup_logging(logging.DEBUG)  # For detailed logs
setup_logging(logging.INFO)   # For standard logs
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

## 📝 License

This project is provided as-is. Please respect Discord's Terms of Service and API usage policies.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Made with ❤️ for Discord automation**
