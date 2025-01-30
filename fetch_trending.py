import requests
import os
from notion_client import Client
from datetime import datetime, timedelta
from datetime import timezone


# GitHub API & Notion API
G_TOKEN = os.getenv("G_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

# GitHub API URL
GITHUB_API_URL = "https://api.github.com/search/repositories"

HEADERS = {"Authorization": f"Bearer {G_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def get_date_range(timeframe):
    """Returns the start date for GitHub search based on timeframe."""
today = datetime.now(timezone.utc).date()
    if timeframe == "daily":
        return today - timedelta(days=1)
    elif timeframe == "weekly":
        return today - timedelta(weeks=1)
    elif timeframe == "monthly":
        return today - timedelta(days=30)
    return today

def fetch_trending_repos(timeframe, language=None):
    """Fetch top 10 trending repositories from GitHub using the Search API."""
    date_range = get_date_range(timeframe)
    query = f"created:>{date_range}"
    if language:
        query += f" language:{language}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 10
    }

    response = requests.get(GITHUB_API_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()["items"]

def get_existing_repos():
    """Fetch existing repository URLs from Notion to avoid duplicates."""
    query = notion.databases.query(database_id=NOTION_DATABASE_ID)
    return {entry["properties"]["URL"]["url"]: entry["id"] for entry in query["results"]}

def update_notion(trending_repos, timeframe, language_label):
    """Update Notion with the latest trending repositories."""
    existing_repos = get_existing_repos()
    new_entries = []

    for repo in trending_repos:
        title = repo["name"]
        stars = repo["stargazers_count"]
        url = repo["html_url"]
        description = repo.get("description", "No description available.")

        if url in existing_repos:
            notion.pages.update(existing_repos[url], properties={"Timeframe": {"select": timeframe}})
        else:
            new_entries.append(url)
            notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties={
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Stars": {"number": stars},
                    "URL": {"url": url},
                    "Timeframe": {"select": timeframe},
                    "New Entry": {"checkbox": True},
                    "Language": {"select": language_label},
                    "Description": {"rich_text": [{"text": {"content": description}}]}
                }
            )

if __name__ == "__main__":
    for timeframe in ["daily", "weekly", "monthly"]:
        # Fetch and update for all languages
        trending_all = fetch_trending_repos(timeframe)
        update_notion(trending_all, timeframe, "All Languages")

        # Fetch and update for Python
        trending_python = fetch_trending_repos(timeframe, "python")
        update_notion(trending_python, timeframe, "Python")
