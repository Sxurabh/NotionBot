import requests
import os
from notion_client import Client
from datetime import datetime, timedelta, timezone

# GitHub API & Notion API Credentials
G_TOKEN = os.getenv("G_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Initialize Notion Client
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

    # Handle HTTP errors gracefully
    if response.status_code != 200:
        print(f"GitHub API error {response.status_code}: {response.text}")
        return []

    return response.json().get("items", [])

def get_existing_repos():
    """Fetch existing repository URLs from Notion to avoid duplicates."""
    try:
        query = notion.databases.query(database_id=NOTION_DATABASE_ID)
        existing_repos = {}
        
        for entry in query["results"]:
            props = entry.get("properties", {})
            
            # Ensure 'URL' property exists
            if "URL" in props and props["URL"].get("url"):
                existing_repos[props["URL"]["url"]] = entry["id"]
        
        return existing_repos
    except Exception as e:
        print(f"Error fetching existing Notion entries: {e}")
        return {}

def update_notion(trending_repos, timeframe, language_label):
    """Update Notion with the latest trending repositories."""
    existing_repos = get_existing_repos()
    new_entries = []

    for repo in trending_repos:
        title = repo["name"]
        stars = repo["stargazers_count"]
        url = repo["html_url"]
        description = repo.get("description", "No description available.")

        # Ensure Timeframe is a valid Notion select option
        if timeframe not in ["daily", "weekly", "monthly"]:
            print(f"Invalid timeframe: {timeframe}")
            continue

        # Update existing repo
        if url in existing_repos:
            try:
                notion.pages.update(
                    page_id=existing_repos[url], 
                    properties={"Timeframe": {"select": {"name": timeframe}}}
                )
            except Exception as e:
                print(f"Error updating Notion entry for {title}: {e}")
        else:
            # Add new repo entry to Notion
            new_entries.append(url)
            try:
                notion.pages.create(
                    parent={"database_id": NOTION_DATABASE_ID},
                    properties={
                        "Name": {"title": [{"text": {"content": title}}]},
                        "Stars": {"number": stars},
                        "URL": {"url": url},
                        "Timeframe": {"select": {"name": timeframe}},
                        "New Entry": {"checkbox": True},
                        "Language": {"select": {"name": language_label}},
                        "Description": {"rich_text": [{"text": {"content": description}}]}
                    }
                )
            except Exception as e:
                print(f"Error creating Notion entry for {title}: {e}")

if __name__ == "__main__":
    for timeframe in ["daily", "weekly", "monthly"]:
        # Fetch and update for all languages
        trending_all = fetch_trending_repos(timeframe)
        update_notion(trending_all, timeframe, "All Languages")

        # Fetch and update for Python
        trending_python = fetch_trending_repos(timeframe, "python")
        update_notion(trending_python, timeframe, "Python")
