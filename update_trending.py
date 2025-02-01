import requests
import os
from bs4 import BeautifulSoup
from notion_client import Client
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

# ADD THIS FUNCTION BACK (WAS MISSING)
def get_trending_repos(timeframe="daily", language=""):
    """Scrape GitHub trending repositories"""
    url = f"https://github.com/trending/{language}?since={timeframe}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    repos = []
    for repo in soup.select("article.Box-row"):
        name = repo.select_one("h2 a").text.strip().replace("\n", "").replace(" ", "")
        desc = repo.select_one("p").text.strip() if repo.select_one("p") else ""
        url = f"https://github.com{repo.select_one('h2 a')['href']}"
        stars = repo.select_one("[aria-label='star']").parent.text.strip().replace(",", "")
        forks = repo.select_one("[aria-label='fork']").parent.text.strip().replace(",", "")
        
        repos.append({
            "name": name,
            "description": desc,
            "url": url,
            "stars": int(stars),
            "forks": int(forks),
            "timeframe": timeframe,
            "language": language.lower() if language else "all"
        })
    return repos

def repo_exists(repo_name, timeframe, category):
    """Check if repo already exists in the database"""
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
