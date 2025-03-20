import requests

# Base URL for MapleStory.io API
BASE_URL = "https://maplestory.io/api/GMS/255"

def get_item_icon_url(item_name):
    # Search for the item
    search_url = f"{BASE_URL}/item?searchFor={item_name}"
    response = requests.get(search_url)

    if response.status_code == 200 and response.json():
        item_data = response.json()[0]  # Take the first result
        item_id = item_data["id"]
        icon_url = f"{BASE_URL}/item/{item_id}/iconRaw"
        return icon_url
    else:
        return "Item not found."

# Example usage:
icon_url = get_item_icon_url("Death's Scythe")
print(icon_url)
