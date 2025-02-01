import requests
import os
from bs4 import BeautifulSoup
from notion_client import Client
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

def repo_exists(repo_name, timeframe, category):
    """Check if repo already exists in the database for the same timeframe/category"""
    response = notion.databases.query(
        NOTION_DATABASE_ID,
        filter={
            "and": [
                {"property": "Repo Name", "title": {"equals": repo_name}},
                {"property": "Timeframe", "select": {"equals": timeframe}},
                {"property": "Category", "select": {"equals": category}}
            ]
        }
    )
    return len(response["results"]) > 0

def add_to_notion(repo, category):
    """Add repo with status tracking"""
    is_new = not repo_exists(repo["name"], repo["timeframe"], category)
    
    properties = {
        "Repo Name": {"title": [{"text": {"content": repo["name"]}}]},
        "Description": {"rich_text": [{"text": {"content": repo["description"]}}]},
        "URL": {"url": repo["url"]},
        "Stars": {"number": repo["stars"]},
        "Forks": {"number": repo["forks"]},
        "Language": {"select": {"name": repo["language"]}},
        "Timeframe": {"select": {"name": repo["timeframe"]}},
        "Category": {"select": {"name": category}},
        "Status": {"select": {"name": "New" if is_new else "Existing"}},
        "First Seen": {"date": {"start": datetime.now().isoformat()}} if is_new else None
    }
    
    # Remove None values
    properties = {k: v for k, v in properties.items() if v is not None}
    
    notion.pages.create(parent={"database_id": NOTION_DATABASE_ID}, properties=properties)

def main():
    timeframes = ["daily", "weekly", "monthly"]
    
    for timeframe in timeframes:
        # All languages
        for repo in get_trending_repos(timeframe)[:10]:
            add_to_notion(repo, "All Languages")
        # Python-only
        for repo in get_trending_repos(timeframe, "python")[:10]:
            add_to_notion(repo, "Python")

if __name__ == "__main__":
    main()

 
