import discord
from discord.ext import commands
from discord import app_commands
import requests
import pandas as pd
import asyncio
import json
import os
from dotenv import load_dotenv 
from datetime import datetime
import re
import time
import urllib.parse

load_dotenv()

# Configuration
APP_ID = "216150"  # App ID for the game you're monitoring (CS:GO)
CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)
DATA_FILE = "steam_market_data.json"
COOKIE = ""  # Add your Steam session cookie here if needed
TOKEN = os.getenv('TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Required for voice state updates

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

# Load items from CSV
def load_items_from_csv():
    try:
        df = pd.read_csv('All_Items.csv')
        # If your CSV has a column with item names, adjust accordingly
        # Assuming the first column contains item names
        items = df.iloc[:, 0].tolist()
        return items
    except Exception as e:
        print(f"Error loading items from CSV: {e}")
        # Return some default items if CSV loading fails
        return ["Dreams & Nightmares Case", "AK-47 | Redline (Field-Tested)", "AWP | Asiimov (Field-Tested)"]

def get_item_price(item_name):
    """
    Fetch the current price of a specific item from the Steam Market
    
    Args:
        item_name (str): The exact name of the item to search for
        
    Returns:
        dict: Item information including price or None if not found
    """
    # URL encode the item name for use in the URL
    encoded_name = requests.utils.quote(item_name)
    
    url = f"https://steamcommunity.com/market/priceoverview/?appid={APP_ID}&currency=1&market_hash_name={encoded_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Cookie": COOKIE
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            return {
                "name": item_name,
                "lowest_price": data.get("lowest_price"),
                "volume": data.get("volume"),
                "median_price": data.get("median_price"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            print(f"Item not found: {item_name}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching item price: {e}")
        return None

def extract_highest_buy_order(data):
    prices = re.findall(r'\$(\d+\.\d+)', data["buy_order_table"])  # Extract prices
    highest_price = max(map(float, prices))  # Convert to float and find max
    return float(highest_price)  # Convert to int


def get_highest_buy_order(item_name, app_id=216150):
    # URL encode the item name
    encoded_item_name = urllib.parse.quote(item_name)
    
    # Steam Community Market itemordershistogram API endpoint
    url = f"https://steamcommunity.com/market/itemordershistogram?country=US&language=english&currency=1&item_nameid=ITEM_NAMEID&two_factor=0"
    
    # First we need to get the item_nameid
    market_page_url = f"https://steamcommunity.com/market/listings/{app_id}/{encoded_item_name}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # First get the market page to extract the item_nameid
        market_response = requests.get(market_page_url, headers=headers)
        
        if market_response.status_code == 429:
            print("Rate limited. Waiting 60 seconds...")
            time.sleep(60)
            return get_highest_buy_order(item_name, app_id)
        
        if market_response.status_code != 200:
            print(f"Failed to get market page with status code: {market_response.status_code}")
            return None
        
        # Extract the item_nameid from the page content
        content = market_response.text
        nameid_start = content.find('Market_LoadOrderSpread(') + len('Market_LoadOrderSpread(')
        if nameid_start == -1 + len('Market_LoadOrderSpread('):
            print(f"Could not find item_nameid for {item_name}")
            return None
        
        nameid_end = content.find(')', nameid_start)
        item_nameid = content[nameid_start:nameid_end].strip()
        
        # Now get the order histogram data
        histogram_url = url.replace('ITEM_NAMEID', item_nameid)
        histogram_response = requests.get(histogram_url, headers=headers)
        
        if histogram_response.status_code == 429:
            print("Rate limited. Waiting 60 seconds...")
            time.sleep(60)
            return get_highest_buy_order(item_name, app_id)
        
        if histogram_response.status_code != 200:
            print(f"Failed to get histogram data with status code: {histogram_response.status_code}")
            return None
        
        histogram_data = histogram_response.json()

        
        if histogram_data.get('success') != 1:
            print(f"API request unsuccessful for {item_name}")
            return None
        
        # Check if there are buy orders
        if histogram_data.get('buy_order_graph') and len(histogram_data['buy_order_graph']) > 0:
           
            highest_price = extract_highest_buy_order(histogram_data)
            return highest_price

    
    except Exception as e:
        print(f"Error: {e}")
        return None




@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Create a modal for item search
class SearchModal(discord.ui.Modal, title="Search Steam Market Items"):
    query = discord.ui.TextInput(
        label="Item Name",
        placeholder="Enter full or partial item name",
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        search_query = self.query.value
        
        # Load all items
        all_items = load_items_from_csv()
        
        # Filter items based on the search query
        matching_items = [item for item in all_items if search_query.lower() in item.lower()]
        
        if not matching_items:
            await interaction.followup.send(f"No items found matching '{search_query}'.")
            return
        
        if len(matching_items) > 10:
            # Show the first 10 results
            results_text = f"Found {len(matching_items)} items matching '{search_query}'. Showing first 10:\n"
            for i, item in enumerate(matching_items[:10], 1):
                results_text += f"{i}. {item}\n"
            
            # Create a button for each result
            view = ResultsView(matching_items[:10])
            await interaction.followup.send(results_text, view=view)
        else:
            # Show all results
            results_text = f"Found {len(matching_items)} items matching '{search_query}':\n"
            for i, item in enumerate(matching_items, 1):
                results_text += f"{i}. {item}\n"
            
            # Create a button for each result
            view = ResultsView(matching_items)
            await interaction.followup.send(results_text, view=view)

# Create buttons for item selection
class ItemButton(discord.ui.Button):
    def __init__(self, item_name, index):
        super().__init__(
            label=f"{index}",
            style=discord.ButtonStyle.primary,
            custom_id=f"item_{index}"
        )
        self.item_name = item_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        item_data = get_item_price(self.item_name)
        
        if item_data:
            embed = discord.Embed(
                title=f"Steam Market Price: {self.item_name}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            if item_data.get("lowest_price"):
                embed.add_field(name="Lowest Price", value=item_data["lowest_price"], inline=True)
            
            if item_data.get("volume"):
                embed.add_field(name="Volume (24h)", value=item_data["volume"], inline=True)
                
            if item_data.get("median_price"):
                embed.add_field(name="Median Price", value=item_data["median_price"], inline=True)

            try:
                buy_order = get_highest_buy_order(self.item_name)
                string_order = "USD$"+str(buy_order)
                embed.add_field(name="Max Buy Order",value=string_order, inline=True)
                    
                embed.set_footer(text=f"Requested by {interaction.user.name}")
            except Exception as e:
                print(e)
        
            # Mention the user in the message content
            await interaction.followup.send(content=f"{interaction.user.mention}, here's your price check:", embed=embed)
        else:
            await interaction.followup.send(f"{interaction.user.mention}, could not retrieve price data for {self.item_name}.", ephemeral=True)

class ResultsView(discord.ui.View):
    def __init__(self, items):
        super().__init__(timeout=60)
        # Add a button for each item
        for i, item in enumerate(items, 1):
            self.add_item(ItemButton(item, i))

@bot.tree.command(name="pricecheck", description="Search and check the price of Steam Market items")
async def pricecheck(interaction: discord.Interaction):
    # Open the search modal
    await interaction.response.send_modal(SearchModal())


# Run the bot
bot.run(TOKEN)