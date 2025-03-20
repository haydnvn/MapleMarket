import requests
import time
import json
import os
from datetime import datetime
import discord
from discord.ext import tasks

# Configuration
APP_ID = "730"  # App ID for the game you're monitoring
CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)
DATA_FILE = "steam_market_data.json"
COOKIE = ""  # Add your Steam session cookie here if needed

# Discord Configuration
DISCORD_BOT_TOKEN = "MTM1MjAxMDk3NDg2MDkzNTM0MA.GsBx5A.ikfKfLLQXb1eq4RMYlNlnqtuGPwEVzz90waKtU"  # Your Discord bot token here
DISCORD_CHANNEL_ID = 501977699800317955  # Channel ID where notifications will be sent (as integer)

# Discord client setup
client = discord.Client(intents=discord.Intents.default())
discord_ready = False

def get_market_listings():
    """
    Fetch current market listings from Steam
    """
    url = f"https://steamcommunity.com/market/search/render/?appid={APP_ID}&norender=1&count=100"
   
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Cookie": COOKIE
    }
   
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market data: {e}")
        return None

def save_data(data):
    """
    Save market data to file
    """
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    """
    Load previously saved market data
    """
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"results": [], "last_check": None}
    return {"results": [], "last_check": None}

def find_new_items(old_data, new_data):
    """
    Compare old and new data to find new listings
    """
    if not old_data["results"] or not new_data["results"]:
        return []
   
    old_item_ids = {item["name"]: item for item in old_data["results"]}
    new_items = []
   
    for item in new_data["results"]:
        item_name = item["name"]
        if item_name not in old_item_ids:
            new_items.append(item)
        # Optional: Check if price changed significantly
        # elif abs(float(item["sell_price"]) - float(old_item_ids[item_name]["sell_price"])) > threshold:
        #    new_items.append(item)
   
    return new_items

def notify_new_items(new_items):
    """
    Notify about new items in console and Discord
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n===== {timestamp} =====")
    print(f"Found {len(new_items)} new items on Steam Market for AppID {APP_ID}")
   
    # Prepare Discord message
    discord_message = f"**Steam Market Update ({timestamp})** 🎮\n"
    discord_message += f"Found {len(new_items)} new items for AppID {APP_ID}\n\n"
    
    for item in new_items:
        item_name = item['name']
        price = item.get('sell_price_text', 'N/A')
        item_url = f"https://steamcommunity.com/market/listings/{APP_ID}/{item_name}"
        
        print(f"- {item_name}: ${price}")
        print(f"  Link: {item_url}")
        
        # Add to Discord message (limiting to 1900 chars to avoid Discord message limit)
        item_info = f"📌 **{item_name}**: ${price}\n{item_url}\n"
        if len(discord_message) + len(item_info) < 1900:
            discord_message += item_info
        else:
            discord_message += "... (more items not shown)"
            break
    
    # Send Discord notification
    if discord_ready:
        send_discord_notification(discord_message)
    else:
        print("Discord client not ready. Notification will be sent once connected.")
        # Store the message to be sent when Discord is ready
        global pending_notification
        pending_notification = discord_message

def send_discord_notification(message):
    """
    Send a notification to Discord
    """
    try:
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            client.loop.create_task(channel.send(message))
        else:
            print(f"Error: Discord channel with ID {DISCORD_CHANNEL_ID} not found.")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def get_recent_items(data, count=5):
    """
    Get the most recent items from the market data
    """
    if not data or "results" not in data or not data["results"]:
        return []
    
    # Sort items by date if available, otherwise just take the first ones
    # Note: Steam's API doesn't always provide a reliable date field,
    # so this is a best-effort approach
    items = data["results"]
    
    # Try to sort by date if available
    if items and len(items) > 0 and "listingdate" in items[0]:
        items.sort(key=lambda x: x.get("listingdate", 0), reverse=True)
    
    # Return the most recent 'count' items
    return items[:min(count, len(items))]

# Initialize pending notification
pending_notification = None

@client.event
async def on_ready():
    """
    Called when the Discord client is ready
    """
    global discord_ready
    print(f"Discord bot connected as {client.user}")
    discord_ready = True
    
    # Send any pending notification
    global pending_notification
    if pending_notification:
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send(pending_notification)
            pending_notification = None
    
    # Send recent items on launch
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("🚀 **Steam Market Monitor Started** 🚀\nFetching most recent items...")
        # We need to use client.loop.create_task for this to avoid blocking
        client.loop.create_task(send_recent_items())
    
    # Start the market check loop
    check_market.start()

async def send_recent_items(count=5):
    """
    Async function to send the most recent items
    """
    # Wait a moment to ensure the startup message is sent first
    await client.wait_until_ready()
    await asyncio.sleep(2)
    
    # Get market data
    data = get_market_listings()
    
    if not data or "results" not in data or not data["results"]:
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send("❌ Failed to fetch market data or no items found.")
        return

    # Get the most recent items
    recent_items = get_recent_items(data, count)
    
    if not recent_items:
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send("❌ No recent items found.")
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\n===== {timestamp} =====")
    print(f"Sending list of {len(recent_items)} most recent items on Steam Market for AppID {APP_ID}")
    
    # Create the message
    message = f"**Most Recent Steam Market Items ({timestamp})** 🎮\n"
    message += f"Total items available: {len(data['results'])}\n"
    message += f"Showing {len(recent_items)} most recent items:\n\n"
    
    for item in recent_items:
        item_name = item['name']
        price = item.get('sell_price_text', 'N/A')
        item_url = f"https://steamcommunity.com/market/listings/{APP_ID}/{item_name}"
        
        message += f"📌 **{item_name}**: ${price}\n{item_url}\n\n"
    
    # Send the message
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(message)
    
    # Save the data
    data["last_check"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_data(data)

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_market():
    """
    Discord task to check the market periodically
    """
    print(f"\nChecking market at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    # Load previous data
    old_data = load_data()
    
    # Get current market data
    new_data = get_market_listings()
    
    if new_data and "results" in new_data:
        # Find new items
        new_items = find_new_items(old_data, new_data)
        
        if new_items:
            notify_new_items(new_items)
        else:
            print("No new items found.")
        
        # Save the new data
        new_data["last_check"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_data(new_data)
    else:
        print("Failed to get market data or invalid response format.")

if __name__ == "__main__":
    try:
        print(f"Starting Steam Market monitor for AppID {APP_ID}")
        print(f"Checking every {CHECK_INTERVAL} seconds")
        print("Connecting to Discord...")
        
        # Check if Discord token is set
        if not DISCORD_BOT_TOKEN:
            print("WARNING: Discord bot token is not set. Please set DISCORD_BOT_TOKEN.")
        
        # Import asyncio for managing async tasks
        import asyncio
        
        # Start the Discord client
        client.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Error: {e}")