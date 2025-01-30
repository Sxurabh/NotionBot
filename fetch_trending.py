import requests
import os
from notion_client import Client

# GitHub Trending API (Unofficial)
TRENDING_API_URL = "https://api.github-trending.com/v1/repositories"

# Notion API
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

def fetch_trending(timeframe, language=""):
    """Fetch top trending GitHub repos for a given timeframe and language."""
    url = f"{TRENDING_API_URL}?language={language}&since={timeframe}"
    response = requests.get(url)
    return response.json()[:10]

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
        stars = repo["stars"]
        url = repo["url"]
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
        trending_all = fetch_trending(timeframe)
        update_notion(trending_all, timeframe, "All Languages")

        # Fetch and update for Python
        trending_python = fetch_trending(timeframe, "python")
        update_notion(trending_python, timeframe, "Python")
