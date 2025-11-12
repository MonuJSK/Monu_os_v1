# Monu OS v1 - Automated Daily Market Update Pipeline

🌟 **An intelligent market oracle that delivers daily insights in Hinglish, powered by AI and automated pipelines.**

Monu OS v1 is a production-ready Python application that automatically fetches market data, calculates technical indicators, generates AI-powered Hinglish market insights, and delivers them via Telegram - all while storing comprehensive data in Google Sheets.

## 🚀 Features

- **Automated Data Pipeline**: Fetches real-time market data for NIFTY, BANKNIFTY, BTCUSDT, and XAUUSD
- **Technical Analysis**: Calculates EMA 20, RSI 14, percentage changes, and volume analysis
- **AI-Powered Insights**: Uses Claude Sonnet 4.5 to generate culturally relevant Hinglish market wisdom
- **Multi-Channel Delivery**: Sends formatted messages to Telegram channels
- **Data Persistence**: Stores all data in Google Sheets with automatic worksheet management
- **Production Ready**: Docker containerization, scheduled workflows, and comprehensive error handling
- **Modular Architecture**: Clean, type-hinted code with comprehensive unit tests

## 📋 Requirements

- Python 3.11+
- Docker (for containerized deployment)
- Google Cloud Platform account (for Sheets API)
- Telegram Bot API access
- TradingView DataFeed credentials
- Anthropic Claude API key (optional, falls back to template messages)

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/monu_os_v1.git
cd monu_os_v1
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# TradingView DataFeed credentials
TVDATA_USERNAME=your_tradingview_username
TVDATA_PASSWORD=your_tradingview_password

# Google Sheets service account
GOOGLE_SA_JSON_PATH=path/to/your/service_account.json
SHEETS_ID=your_google_sheets_spreadsheet_id

# Telegram bot configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Claude API (optional)
CLAUDE_API_KEY=your_claude_api_key
```

### 3. Google Cloud Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Google Sheets API**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and enable it

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Give it a name like "monu-os-service"
   - Grant "Editor" role for Google Sheets access

4. **Generate JSON Key**
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key" > "JSON"
   - Download the JSON file and place it in your project root

5. **Create Google Sheet**
   - Create a new Google Sheet
   - Copy the spreadsheet ID from the URL (the long string between `/d/` and `/edit`)
   - Share the sheet with your service account email (found in the JSON file)

### 4. Telegram Bot Setup

1. **Create a Bot**
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow instructions
   - Save the bot token

2. **Get Chat ID**
   - Create a private channel or group
   - Add your bot as administrator
   - Send a message to the channel
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find the chat ID in the response

### 5. TradingView DataFeed Setup

1. Sign up for TradingView account if you don't have one
2. Get your credentials from TradingView settings
3. Note: Free accounts have rate limits

### 6. Claude API Setup (Optional)

1. Sign up for Anthropic Claude API access
2. Get your API key from the dashboard
3. If not provided, the system will use fallback template messages

## 🧪 Testing

### Run Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_fetcher.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Test Connections

```bash
# Test all external API connections
python src/cli.py test

# Test with debug logging
python src/cli.py test --log-level DEBUG
```

## 🚀 Running the Pipeline

### Manual Run

```bash
# Run the complete daily pipeline
python src/cli.py run

# Run with custom log level
python src/cli.py run --log-level DEBUG
```

### Docker Run

```bash
# Build the image
docker build -t monu-os-v1 .

# Run the container
docker run --rm \
  --env-file .env \
  -v $(pwd)/service_account.json:/app/service_account.json:ro \
  monu-os-v1
```

## 📊 Data Structure

### Google Sheets Worksheets

1. **RawData**: Timestamped OHLCV data with calculated indicators
   - Columns: timestamp, symbol, open, high, low, close, volume, pct_change, vol_change_pct, ema_20, rsi_14, recent_high, recent_low

2. **Summary**: Daily market summary
   - Columns: date, total_symbols, gainers, losers, high_volume, timestamp

3. **Config**: Configuration storage (for future extensibility)

## 🔄 Automation

### GitHub Actions (Daily Schedule)

The pipeline runs automatically every day at 03:30 UTC (9:00 AM IST).

**Setup GitHub Secrets:**
- `TVDATA_USERNAME`
- `TVDATA_PASSWORD`
- `GOOGLE_SA_JSON` (contents of service account JSON file)
- `SHEETS_ID`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `CLAUDE_API_KEY` (optional)

### Railway Deployment

```bash
# Use the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Update the placeholders in `scripts/deploy.sh` with your actual values.

## 📝 Customization

### Adding New Symbols

Edit `src/fetcher.py`:

```python
DEFAULT_SYMBOLS = ['NIFTY', 'BANKNIFTY', 'BTCUSDT', 'XAUUSD', 'YOUR_NEW_SYMBOL']
DEFAULT_EXCHANGES = ['NSE', 'NSE', 'BINANCE', 'FX_IDC', 'YOUR_EXCHANGE']
```

### Modifying Indicators

Add new calculations in `MarketDataFetcher.calculate_indicators()`:

```python
def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
    indicators = {}

    # Add your custom indicator
    indicators['my_indicator'] = self._calculate_my_indicator(data)

    return indicators
```

### Custom Oracle Messages

Edit `example_prompt_template.txt` to customize the Claude prompt for different styles of market wisdom.

## 🛡️ Security Notes

- **Never commit secrets**: All sensitive data is read from environment variables
- **Service account security**: Limit Google service account to only necessary permissions
- **API rate limiting**: Built-in safeguards prevent API abuse
- **Error handling**: Comprehensive error handling prevents data loss
- **Logging**: All operations are logged for audit trails
- **Container security**: Runs as non-root user in Docker

## 🐛 Troubleshooting

### Common Issues

1. **Google Sheets Permission Denied**
   - Ensure service account JSON is correct
   - Check that sheet is shared with service account email
   - Verify Sheets API is enabled

2. **Telegram Messages Not Sending**
   - Confirm bot token is valid
   - Check chat ID is correct
   - Ensure bot is added to the channel/group

3. **TradingView Data Fetching Issues**
   - Verify credentials are correct
   - Check rate limits on free accounts
   - Some exchanges may have restrictions

4. **Claude API Errors**
   - Verify API key is valid
   - Check API quota/limits
   - System falls back to template messages

### Debug Mode

```bash
# Run with maximum logging
python src/cli.py run --log-level DEBUG

# Check logs
tail -f monu_os.log
```

## 📈 Monitoring

- **Logs**: All operations logged to `monu_os.log`
- **Google Sheets**: Real-time data monitoring
- **Telegram**: Immediate notification delivery
- **Health Checks**: Docker health checks for container status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- TradingView for market data access
- Anthropic for Claude AI
- Google Cloud for Sheets API
- Telegram for bot API

---

**Made with ❤️ for the Indian investor community**

*Remember: "Markets ki tarah life bhi ups and downs deti hai, but consistent investing always pays off!" 🚀*
