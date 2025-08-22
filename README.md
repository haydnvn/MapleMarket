# Steam Market Price Checker Discord Bot

A Discord bot that allows users to search and check current Steam Market prices for Maplestory items. The bot provides real-time pricing data including lowest price, volume, median price, and highest buy orders.

## Features

- **Interactive Search**: Use slash commands to search for items with a modal interface
- **Real-time Pricing**: Fetches current Steam Market data including:
  - Lowest selling price
  - 24-hour volume
  - Median price
  - Highest buy order
- **Item Database**: Loads items from a CSV file for quick searching
- **User-friendly Interface**: Clean embeds with item thumbnails and clickable buttons
- **Command Logging**: Tracks usage for analytics
- **Rate Limit Handling**: Automatically handles Steam API rate limits

## Setup

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Steam Market access (no API key required)

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory:
```env
TOKEN=your_discord_bot_token_here
```

4. Ensure your `All_Items.csv` file contains the items you want to track (one item per line).

### Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token to your `.env` file
4. Invite the bot to your server with the following permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Attach Files

## Usage

### Commands

- `/pricecheck` - Opens a search modal to find and check item prices

### How to Use

1. Type `/pricecheck` in any channel
2. Enter the item name (full or partial) in the search modal
3. Select from the search results
4. Click the price button to get current market data

## Configuration

### Environment Variables

- `TOKEN` - Your Discord bot token (required)

### Files

- `All_Items.csv` - Contains the list of items to search through
- `command_logs.csv` - Automatically generated log of bot usage
- `pfp.png` - Bot profile picture (optional)

### Customization

You can modify the following constants in `bot.py`:

- `APP_ID` - Steam App ID (default: 216150 for CS:GO)
- `CHECK_INTERVAL` - Price check interval in seconds (default: 300)
- `COOKIE` - Steam session cookie if needed for authenticated requests

## Data Sources

The bot fetches data from:
- Steam Community Market API for pricing data
- Steam Market pages for buy order information
- MapleStory.io API for item thumbnails (fallback)

## Rate Limiting

The bot includes built-in rate limit handling:
- Automatically waits when Steam API returns 429 status
- Limits search results to prevent API overload
- Implements request delays to avoid being blocked

## Logging

All command usage is logged to `command_logs.csv` with:
- Username
- Server name
- Item searched
- Timestamp

## Troubleshooting

### Common Issues

1. **Bot not responding to slash commands**
   - Ensure the bot has been invited with proper permissions
   - Check that slash commands are synced (happens automatically on startup)

2. **Price data not loading**
   - Steam Market may be temporarily unavailable
   - Check your internet connection
   - Verify the item name exists on Steam Market

3. **Items not found in search**
   - Ensure `All_Items.csv` contains the items you're looking for
   - Check for typos in item names
   - Items must match Steam Market naming exactly

### Error Messages

- "No items found matching..." - Item not in your CSV database
- "Could not retrieve price data..." - Steam Market API error
- "Rate limited. Waiting..." - Temporary Steam API limit (automatic retry)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Disclaimer

This bot is for educational and informational purposes only. Steam Market prices are subject to change and the bot provides no guarantees about price accuracy. Always verify prices on the official Steam Market before making any trading decisions.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.