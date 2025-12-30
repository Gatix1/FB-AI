import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

if not API_KEY or not SEARCH_ENGINE_ID:
    print("[WARNING] Google Custom Search API credentials not found. Dynamic info search will not work.")
    print("Please set GOOGLE_CUSTOM_SEARCH_API_KEY and SEARCH_ENGINE_ID in your .env file.")


def fetch_dynamic_info(query: str) -> str:
    """
    Takes a raw query string, performs a Google Custom Search,
    and returns a formatted summary of the top 3 results.
    """
    if not API_KEY or not SEARCH_ENGINE_ID:
        return "Sorry, web search is not configured. Please set up Google Custom Search API credentials."
    
    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": 3
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Sorry, I couldn't connect to the search service: {e}"

    except Exception as e:
        return f"Sorry, there was an error processing the search results: {e}"
    
    if "items" not in data:
        error_msg = data.get("error", {}).get("message", "Unknown error")
        return f"No results found. Error: {error_msg}"

    results_text = "Top Search Results:\n\n"

    for item in data["items"]:
        title = item.get("title", "No title")
        snippet = item.get("snippet", "No description")
        link = item.get("link", "")
        results_text += f"🔹 {title}\n{snippet}\n{link}\n\n"

    return results_text


# Test for debugging
if __name__ == "__main__":
    print(fetch_dynamic_info("latest news"))
