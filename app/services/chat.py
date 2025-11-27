# app/services/chat.py

from app.services.document_ingestion import DocumentIngestionService
from app.services.question_answer import QuestionAnswerService
from app.services.vector_db import VectorDBService
from app.schemas.chat import ChatRequest, ChatResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import CohereRerank
from app.core.config import settings
from datetime import datetime
from app.main import manager
from datetime import datetime
from typing import List, Dict
import uuid
import requests


# from app.core.logging_config import logging
import os
from app.mongodb import MongoDBClient

# manager = ConnectionManager()

# logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY
        self.document_service = DocumentIngestionService()
        self.qa_service = QuestionAnswerService()
        self.vector_db_service = VectorDBService()
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        self.reranker = CohereRerank(model="rerank-english-v2.0")
        self.mongo_client = MongoDBClient()
        self.collection = self.mongo_client.get_collection() 



    async def insert_chat_data(self, chat_request: ChatRequest, chat_response: ChatResponse):
        try:
            # Generate a unique ID using UUID
            unique_id_sender = str(uuid.uuid4())
            unique_id_assistant = str(uuid.uuid4())

            # Prepare data for insertion
            chat_sender_data = {
                "text": chat_request.get('query'),
                "sender": "user",
                "is_completed": True,
                "s3_image_link": None,
                "id": unique_id_sender,  # Unique ID for sender
                "conversation_id": chat_request.get('conversation_id'),
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            }

            chat_assistant_data = {
                "text": chat_response.answer,
                "sender": "assistant",
                "is_completed": True,
                "s3_image_link": None,
                "id": unique_id_assistant,  # Unique ID for assistant
                "conversation_id": chat_request.get('conversation_id'),
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            }

            # Insert both chat sender and assistant data into MongoDB
            result_sender = self.collection.insert_one(chat_sender_data)
            chat_sender_data["_id"] = str(result_sender.inserted_id)

            result_assistant = self.collection.insert_one(chat_assistant_data)
            chat_assistant_data["_id"] = str(result_assistant.inserted_id)
            print("Chat data inserted successfully.")

            # Prepare broadcast data containing both sender and assistant data as objects
            broadcast_data = [
                chat_sender_data,
                chat_assistant_data
            ]

            # Send the broadcast to all connected clients in the conversation
            try:
                await manager.broadcast({"status": "new_message", "data": broadcast_data})
            except Exception as e:
                print("WebSocket connection closed before broadcasting:", e)

        except Exception as e:
            print("Error inserting chat data:", e)

    async def get_recent_conversation(self, conversation_id: int, limit: int = 2) -> List[Dict]:
        """Fetch the latest 'limit' messages for a specific conversation."""
        try:
            recent_messages = list(
                self.collection.find({"conversation_id": conversation_id})
                .sort("timestamp", -1)  # Descending order
                .limit(limit)
            )
            # Return messages in ascending order for coherent context
            return recent_messages[::-1]  # Reverse to maintain the chronological order
        except Exception as e:
            print(f"Error retrieving recent messages: {e}")
            return []

    async def get_messages_ascending(self, conversation_id: int) -> List[Dict]:
        try:
            # Query to fetch messages for a specific conversation ID in ascending order check
            messages = list(
                self.collection.find({"conversation_id": conversation_id})
                .sort("timestamp", 1)  # -1 for ascending order
            )
        
            # print(f"messages: {messages}")  # Print the raw messages for debugging
            return [
                {
                    "text": item["text"],
                    "sender": item["sender"],
                    "is_completed": item["is_completed"],
                    "s3_image_link": item["s3_image_link"],
                    "conversation_id": item["conversation_id"],
                    "id": item["id"],
                    "_id": str(item["_id"]),  # Convert ObjectId to string
                }
                for item in messages  # Changed 'message' to 'item' for clarity
            ]
        except Exception as e:
            print(f"Error retrieving messages: {e}")
            # raise HTTPException(status_code=500, detail="Failed to retrieve messages.")

    async def generate_response(self, chat_request: ChatRequest) -> ChatResponse:
        try:
            # Fetch recent conversation history for context
            recent_conversation = await self.get_recent_conversation(chat_request.get('conversation_id'))

            print("recent_conversation")

            # Prepare recent conversation text to add to context
            conversation_history = "\n".join(
                [f"{msg['sender']}: {msg['text']}" for msg in recent_conversation]
            )

            # Fetch relevant documents and rerank them
            relevant_docs = await self.vector_db_service.search_documents(
                chat_request.get('organization_id'),
                chat_request.get('query'),
                k=10
            )
            reranked_docs = self._rerank_documents(chat_request.get('query'), relevant_docs)

            # Fetch relevant questions
            relevant_questions = await self.qa_service.get_relevant_questions(chat_request)

            # Prepare context with conversation history
            context = f"Recent conversation:\n{conversation_history}\n\n" \
                    f"{self._prepare_context(reranked_docs, relevant_questions)}"

            # Generate response with a more flexible prompt for testing
            prompt = f"""
You are a helpful AI assistant. When relevant, use the following context to answer the user's question accurately and concisely. If the context doesn't apply or isn't available, answer based on general knowledge.

Context:
{context}

User's question: {chat_request.get('query')}

If the question connects to any prior conversation or context, use that to inform your answer. Otherwise, rely on general knowledge to respond accurately.
"""
            
            print(f"prompt{prompt}")
            print("promptcompleted")
            response = self.llm.invoke(prompt)
            response_str = response.content if isinstance(response.content, str) else str(response.content)

            chat_response = ChatResponse(
                answer=response_str,
                relevant_docs=[doc.page_content for doc in reranked_docs],
                relevant_questions=[q.page_content for q in relevant_questions]
            )

            # Insert new chat data into MongoDB
            await self.insert_chat_data(chat_request, chat_response)
            return chat_response

        except Exception as e:
            print(f"Error generating chat response: {str(e)}")
            raise

    def _rerank_documents(self, query, docs):
        try:
            documents = [doc.page_content for doc in docs]
            reranked_results = self.reranker.rerank(
                documents=documents,
                query=query,
                top_n=5  # Return top 5 most relevant results
            )

            reranked_docs = []
            for item in reranked_results:
                idx = item.get('index')
                relevance_score = item.get('relevance_score')
                if idx is None or relevance_score is None:
                    continue
                doc = docs[idx]
                doc.metadata['relevance_score'] = relevance_score
                if relevance_score > 0.20:
                    reranked_docs.append(doc)

            return reranked_docs
        except Exception as e:
            # logger.error(f"Error in document reranking: {str(e)}")
            return docs  # Return original docs if reranking fails

    def _prepare_context(self, docs, questions):
        context = "Relevant questions and answers:\n"
        for idx, question in enumerate(questions, 1):
            context += f"{question.page_content}\n\n"
        
        context += "Relevant documents:\n"
        for idx, doc in enumerate(docs, 1):
            context += f"{idx}. {doc.page_content}\n\n"
        
        return context