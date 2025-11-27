from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List, Optional
import httpx
import re
from datetime import datetime, timedelta
from app.core.config import settings

app = FastAPI()
router = APIRouter()

class SlackMessage(BaseModel):
    subtype: Optional[str] = None
    text: Optional[str] = None
    ts: Optional[str] = None

class SlackResponse(BaseModel):
    ok: bool
    messages: List[SlackMessage]

class PipelineRequest(BaseModel):
    channel_id: str
    pipeline_name: str
    start_time: Optional[str] = None  # Format: "YYYY-MM-DD HH:MM:SS"
    end_time: Optional[str] = None    # Format: "YYYY-MM-DD HH:MM:SS"

class PipelineInfo(BaseModel):
    pipeline_name: str
    timestamp: str
    full_message: str

class ProcessorResponse(BaseModel):
    status: str
    pipeline_info: List[PipelineInfo]

class SlackMessageProcessor:
    def __init__(self, pipeline_name: str):
        self.pipeline_url_pattern = r'https://app\.harness\.io/ng/account/[^/]+/module/cd/orgs/[^/]+/projects/[^/]+/pipelines/([^/]+)/pipeline-studio'
        self.pipeline_name = pipeline_name

    def extract_pipeline_info(self, messages: List[dict]) -> List[dict]:
        pipeline_info = []
        for message in messages:
            if message.get('subtype') == 'bot_message' and 'text' in message:
                text = message['text']
                match = re.search(self.pipeline_url_pattern, text)
                if match and self.pipeline_name in text:
                    pipeline_info.append({
                        'pipeline_name': match.group(1),
                        'timestamp': message.get('ts', ''),
                        'full_message': text
                    })
        return pipeline_info

    async def process_pipeline_messages(self, request: PipelineRequest):
        try:
            current_time = datetime.now()
            end_time = datetime.strptime(request.end_time, "%Y-%m-%d %H:%M:%S") if request.end_time else current_time
            start_time = datetime.strptime(request.start_time, "%Y-%m-%d %H:%M:%S") if request.start_time else end_time - timedelta(days=10)
            
            oldest = str(int(start_time.timestamp()))
            latest = str(int(end_time.timestamp()))

            slack_url = "https://slack.com/api/conversations.history"
            params = {"channel": request.channel_id, "limit": 200, "oldest": oldest, "latest": latest}
            headers = {"Authorization": f"Bearer {settings.SLACK_APP_TOKEN}", "Content-Type": "application/x-www-form-urlencoded"}

            async with httpx.AsyncClient() as client:
                response = await client.get(slack_url, params=params, headers=headers)
                response.raise_for_status()
                slack_data = response.json()
                if not slack_data.get("ok"):
                    raise HTTPException(status_code=400, detail=f"Slack API error: {slack_data.get('error', 'Unknown error')}")

                pipeline_info = self.extract_pipeline_info(slack_data.get("messages", []))
                return ProcessorResponse(status="success", pipeline_info=pipeline_info)

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Slack API request failed: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))