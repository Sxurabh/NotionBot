import requests
import os
from bs4 import BeautifulSoup
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")


notion = Client(auth=NOTION_TOKEN)



def get_trending_repos(timeframe="daily", language=""):
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

def add_to_notion(repo):
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "Repo Name": {"title": [{"text": {"content": repo["name"]}}]},
            "Description": {"rich_text": [{"text": {"content": repo["description"]}}]},
            "URL": {"url": repo["url"]},
            "Stars": {"number": repo["stars"]},
            "Forks": {"number": repo["forks"]},
            "Language": {"select": {"name": repo["language"]}},
            "Timeframe": {"select": {"name": repo["timeframe"]}},
            "Category": {"select": {"name": "Python" if repo["language"] == "python" else "All Languages"}}
        }
    )

def main():
    timeframes = ["daily", "weekly", "monthly"]
    
    # Optional: Clear old entries (uncomment if needed)
    # existing = notion.databases.query(NOTION_DATABASE_ID).get("results")
    # for page in existing: notion.pages.update(page["id"], archived=True)
    
    for timeframe in timeframes:
        # All languages
        for repo in get_trending_repos(timeframe)[:10]:
            add_to_notion(repo)
        # Python-only
        for repo in get_trending_repos(timeframe, "python")[:10]:
            add_to_notion(repo)

if __name__ == "__main__":
    main()
