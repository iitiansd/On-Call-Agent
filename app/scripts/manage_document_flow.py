from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel
import os

from app.services.document_ingestion import DocumentIngestionService
from app.services.vector_db import VectorDBService
from app.services.chat import ChatService
from app.services.jiratool import JiraHandler
from app.services.slack import SlackHandler
from app.services.github import GitHubService
from app.services.observe_logs import ObserveLogsFetcher
from app.services.slack_fetch import SlackMessageProcessor
# from app.scripts.connection_manager import ConnectionManager  # Import ConnectionManager
from app.main import manager
from app.services.question_answer import QuestionAnswerService
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows all origins. You can specify specific origins if needed.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# manager = ConnectionManager()
# Predefined path for the PDF file
PDF_FILE_PATH = "ENG-Platform Engineering Runbooks.pdf"
class QuestionAnswerRequest(BaseModel):
    question: str
    answer: str
    organization_id: str

class ChatRequest(BaseModel):
    query: str
    organization_id: str    
    conversation_id: int
    sender: str

class SlackQueryRequest(BaseModel):
    tool_name: str
    query: str


class ObserveLogsRequest(BaseModel):
    observe_logs_url: str


class PipelineRequest(BaseModel):
    channel_id: str
    pipeline_name: str
    start_time: Optional[str] = None  # Format: "YYYY-MM-DD HH:MM:SS"
    end_time: Optional[str] = None    # Format: "YYYY-MM-DD HH:MM:SS"
# Endpoint to process the predefined document and insert into vector DB
@app.post("/upload-document/")
async def upload_document(organization_id: str):
    try:
        # Check if file exists
        if not os.path.exists(PDF_FILE_PATH):
            raise HTTPException(status_code=404, detail="PDF file not found")

        ingestion_service = DocumentIngestionService()
        vector_db_service = VectorDBService()

        print(f"Processing document: {PDF_FILE_PATH} for organization: {organization_id}")
        processed_docs = await ingestion_service.process_document(PDF_FILE_PATH, organization_id)

        print("Inserting documents into vector database...")
        await vector_db_service.insert_documents(processed_docs)
        print("Document insertion completed.")

        return {"status": "success", "message": "Document processed and inserted into vector DB."}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document.")

# Chat command to generate responses
@app.post("/chat/")
async def chat_interaction(request: ChatRequest):
    try:
        chat_service = ChatService()

        print(f"Generating response for: {request.query}")
        chat_request = {"query": request.query, "organization_id": request.organization_id, "conversation_id": request.conversation_id, "sender": request.sender}
        response = await chat_service.generate_response(chat_request)
        
        return {"status": "success", "response": response}
    except Exception as e:
        print(f"Error during chat interaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate chat response.")


@app.get("/chat/messages/{conversation_id}")
async def get_messages(conversation_id: int):
    chat_service = ChatService()
    try:
        # Retrieve messages in ascending order by timestamp
        messages = await chat_service.get_messages_ascending(conversation_id)
        return {"status": "success", "messages": messages}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@app.websocket("/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: int):
    await manager.connect(websocket)
    try:
        chat_service = ChatService()

        # Fetch chat history in ascending order by timestamp
        chat_history = await chat_service.get_messages_ascending(conversation_id)

        # Prepare response
        data = [
            {
                "conversation_id": item["conversation_id"],
                "text": item["text"],
                "sender": item["sender"],
                "is_completed": item["is_completed"],
                "s3_image_link": item["s3_image_link"],
                "id": item["id"]
            }
            for item in chat_history
        ]
        # Send chat history to the connected client
        await manager.send_personal_message({"status": "success", "data": data}, websocket)

        while True:
            # Keep the WebSocket connection alive
            data = await websocket.receive_text()
            # Optionally, handle incoming messages if needed

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/add-question-answer/")
async def add_question_answer(request: QuestionAnswerRequest):
    try:
        qa_service = QuestionAnswerService()
        print(f"Adding question: {request.question} with answer: {request.answer}")

        question_answer_create = {
            "question": request.question,
            "answer": request.answer,
            "organization_id": request.organization_id
        }
        await qa_service.add_question_answer(question_answer_create)
        
        return {"status": "success", "message": "Question and answer added to the vector DB."}
    except Exception as e:
        print(f"Error adding question and answer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add question and answer.")


@app.get("/jirafetch/{issue_id}")
def get_jira_details(issue_id: str):
    jira_service = JiraHandler()
    try:
        # Retrieve messages in ascending order by timestamp
        messages = jira_service.get_jira_details(issue_id)
        return {"status": "success", "messages": messages}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@app.get("/previous_comments")
def search_issues_by_summary(query_summary: str = Query(..., description="Summary of the issue to search for")):
    jira_service = JiraHandler()
    try:
        # Retrieve messages in ascending order by timestamp
        messages = jira_service.search_issues_by_summary(query_summary)
        return {"status": "success", "messages": messages}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

        
@app.post("/fetch_observe_logs")
def fetch_observe_logs(request: ObserveLogsRequest):
    observe_fetcher = ObserveLogsFetcher()
    try:
        logs = observe_fetcher.fetch_logs(request.observe_logs_url)
        return {"status": "success", "logs": logs}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")



@app.post("/generate-query/")
async def slack_query_generator(request: SlackQueryRequest):
    try:
        if request.tool_name != "slack_self_querying_keyword search":
            raise HTTPException(status_code=400, detail="Invalid tool name")

        slack_handler = SlackHandler()
        response = slack_handler._self_querying_over_slack_search(request.query)

        return {"status": "success", "message": "Query processed successfully", "data": response}

    except Exception as e:
        print(f"Error processing Slack query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process Slack query.")

@app.post("/slack-query/")
async def slack_query_generator(request: Dict):
    try:
        # if request.tool_name != "slack_self_querying_keyword search":
        #     raise HTTPException(status_code=400, detail="Invalid tool name")
 
        slack_handler = SlackHandler()
        response = await slack_handler.search_slack_messages(
            keyword="Cronjob failure monitor for cronjob/alerts-v2-send-notifications",
            from_user="john",
            in_channel="platinum-platform",
            after_date="2025-01-01",
            before_date="2025-02-01"
        )

        return {"status": "success", "message": "Query processed successfully", "data": response}

    except Exception as e:
        print(f"Error processing Slack query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process Slack query.")


@app.get("/latest-changes")
async def latest_changes(branch: str):
    try:
        github_handler = GitHubService()
        response = await GitHubService.get_latest_commit(branch)
        return response

    except Exception as e:
        print(f"Error processing github query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process github query.")


@app.post("/slack-pipeline-messages/")
async def slack_pipeline_messages(request: PipelineRequest):
    try:
        slack_handler = SlackMessageProcessor()
        response = await slack_handler.process_pipeline_messages(request)
        return {"status": "success", "message": "Query processed successfully", "data": response.dict()}
    except Exception as e:
        print(f"Error processing Slack query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process Slack query.")