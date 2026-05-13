import requests
from urllib.parse import quote


def fetch_wikipedia_summary(title):
    """
    Fetch animal summary and image from Wikipedia.
    Example title: Tiger, Lion, Blue whale, Bald eagle
    """

    if not title:
        return None

    encoded_title = quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

    headers = {
        "User-Agent": "SearchWilds/1.0 (animal research website)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=8)

        if response.status_code != 200:
            return None

        data = response.json()

        return {
            "title": data.get("title", ""),
            "summary": data.get("extract", ""),
            "image_url": data.get("thumbnail", {}).get("source", ""),
            "page_url": data.get("content_urls", {})
                            .get("desktop", {})
                            .get("page", ""),
        }

    except requests.RequestException:
        return None