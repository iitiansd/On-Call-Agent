import os
from fastapi import FastAPI, HTTPException, Query
from app.core.config import settings
import httpx

app = FastAPI()

# GitHub API Credentials
GIT_USERNAME = settings.GIT_USERNAME
GIT_PAT = settings.GIT_PAT
REPO_OWNER = settings.REPO_OWNER
REPO_NAME = settings.REPO_NAME

class GitHubService:
    BASE_URL = "https://api.github.com/repos"

    def __init__(self):
        # Store API key (if needed for OpenAI, unrelated to GitHub API)
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

    @classmethod
    async def get_latest_commit(cls, branch: str = "develop"):
        url = f"{cls.BASE_URL}/{REPO_OWNER}/{REPO_NAME}/commits"
        headers = {
            "Authorization": f"Bearer {GIT_PAT}",
            "Accept": "application/vnd.github.v3+json",
        }
        params = {"sha": "develop"}

        print(f"Fetching commits from URL: {url}")
        print(f"With params: {params}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                print(f"Response Status: {response.status_code}")
                print(f"Response Content: {response.text}")  # Print raw response for debugging
                
                response.raise_for_status()
                data = response.json()

                if not data:
                    raise HTTPException(status_code=404, detail="No commits found for the specified branch")

                latest_commit = data[0]  # Get the most recent commit
                
                return {
                    "repository": f"{REPO_OWNER}/{REPO_NAME}",
                    "branch": branch,
                    "latestCommit": latest_commit["sha"],
                    "commitMessage": latest_commit["commit"]["message"],
                    "author": latest_commit["commit"]["author"]["name"],
                    "date": latest_commit["commit"]["author"]["date"],
                }

        except httpx.HTTPStatusError as e:
            print(f"HTTPStatusError: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# @app.get("/latest-changes")
# async def latest_changes(branch: str = Query(default="master")):
#     github_service = GitHubService()
#     return await github_service.get_latest_commit(branch)