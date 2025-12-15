import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")


def fetch_dynamic_info(query: str) -> str:
    """
    Takes a raw query string, performs a Google Custom Search,
    and returns a formatted summary of the top 3 results.
    """
    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": 3
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" not in data:
        return "No results found or API quota exceeded."

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
