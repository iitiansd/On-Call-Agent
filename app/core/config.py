from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Knowledge Intelligence"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CHROME_DB_URI: str = "http://localhost:8123"  # For local mock DB
    UNSTRUCTURED_API_KEY: str = "your_unstructured_api_key"
    UNSTRUCTURED_API_URL: str = "http://localhost:12012"  # Mock this for local testing
    COHERE_API_KEY: str = ""  # Mock API key
    JIRA_API_TOKEN: str = ""
    JIRA_EMAIL: str = ""
    SLACK_TOKEN: str = ""
    OBSERVE_API_KEY: str = ""
    SLACK_APP_TOKEN:str = ""


    GIT_USERNAME: str = ""
    GIT_PAT: str = ""
    REPO_OWNER: str = "6si" 
    REPO_NAME: str = "ntropy"
 
    class Config:
        env_file = ".env"

settings = Settings()
