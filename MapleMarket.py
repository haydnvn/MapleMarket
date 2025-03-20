import requests
import time
import json
import os
from datetime import datetime

# Configuration
APP_ID = "216150"  # App ID for the game you're monitoring
CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)
DATA_FILE = "steam_market_data.json"
COOKIE = ""  # Add your Steam session cookie here if needed

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
    Notify about new items (customize this function based on how you want to be notified)
    """
    print(f"\n===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    print(f"Found {len(new_items)} new items on Steam Market for AppID {APP_ID}")
    
    for item in new_items:
        print(f"- {item['name']}: ${item.get('sell_price_text', 'N/A')}")
        print(f"  Link: https://steamcommunity.com/market/listings/{APP_ID}/{item['name']}")
    
    # You could add other notification methods here:
    # - Send an email
    # - Push notification
    # - Discord webhook
    # - Telegram message
    # etc.

def main():
    print(f"Starting Steam Market monitor for AppID {APP_ID}")
    print(f"Checking every {CHECK_INTERVAL} seconds")
    
    while True:
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
        
        # Wait for next check
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")