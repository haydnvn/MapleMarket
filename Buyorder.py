import requests
import json
import time
import urllib.parse
import re


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

# Example usage
if __name__ == "__main__":

    #make it search for any item where its >4????
    item_name = "Round Rabbit-Eared Glasses"
    result = get_highest_buy_order(item_name)
    
    print(result)