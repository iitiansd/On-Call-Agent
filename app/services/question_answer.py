# app/services/question_answer.py

from app.core.db import db_manager
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_cohere import CohereRerank
from app.core.config import settings
from langchain.schema import Document
from app.schemas.question_answer import QuestionAnswerCreate, QuestionAnswerSearch, QuestionAnswerResponse
from app.schemas.chat import ChatRequest
from typing import List, Tuple, Union
import uuid
import os
# from app.core.logging_config import logging
# from app.core.exceptions import AppException

# logger = logging.getLogger(__name__)
class QuestionAnswerService:
    def __init__(self):
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY
        self.collection_name = "questions_answers"
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_document")
        self.reranker = CohereRerank(model="rerank-english-v2.0")

    async def add_question_answer(self, qa_data: QuestionAnswerCreate) -> QuestionAnswerResponse:
        with db_manager.get_client() as client:
            if not client:
                raise Exception("Failed to connect to the database")

            vector_store = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )

            # Check for similar questions
            similar_questions = vector_store.similarity_search_with_score(
                qa_data.get('question'),
                k=1,
                filter={"organization_id": qa_data.get('organization_id')}
            )

            # logger.info(f"Similar questions: {similar_questions}")
            # print("debug 1")

            if similar_questions and similar_questions[0][1] < 0.25:  # Adjust threshold as needed
                # Update existing question
                existing_doc = similar_questions[0][0]
                updated_content = await self.merge_questions(existing_doc.page_content, qa_data.get('question'))
                existing_doc.page_content = updated_content
                vector_store.update_document(document_id=existing_doc.metadata['id'], document=existing_doc)
                return QuestionAnswerResponse(id=existing_doc.metadata['id'], question=qa_data.get('question'), answer=qa_data.get('answer'), organization_id=qa_data.get('organization_id'))
            else:
                # Add new question
                qa_id = str(uuid.uuid4())
                # print("debug 2")
                content = f"""Q: {qa_data.get('question')}A: {qa_data.get('answer')}"""
                new_doc = Document(
                    page_content=content,
                    metadata={"id": qa_id, "organization_id": qa_data.get('organization_id')},
                    id=qa_id
                )
                vector_store.add_documents(
                    documents=[new_doc],
                    ids=[qa_id]
                )
                return QuestionAnswerResponse(id=qa_id, question=qa_data.get('question'), answer=qa_data.get('answer'), organization_id=qa_data.get('organization_id'))

    async def get_relevant_questions(self, search_params: Union[QuestionAnswerSearch, ChatRequest]) -> List[Document]:
        with db_manager.get_client() as client:
            if not client:
                raise Exception("Failed to connect to the database")

            vector_store = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )

            results = vector_store.similarity_search_with_score(
                search_params.get('query'),
                k=20,
                filter={"organization_id": search_params.get('organization_id')}
            )

            if not results:
                # logger.info("No questions found in initial search")
                return []

            # logger.info(f"Retrieved {results} questions from vector store")

            documents = [doc.page_content for doc, _ in results]
            try:
                reranked_results = self.reranker.rerank(
                    documents=documents,
                    query=search_params.get('query'),
                    top_n=10  # Return top 10 most relevant results
                )
            except Exception as e:
                logger.error(f"Reranking failed: {str(e)}")
                # raise AppException(status_code=500, detail="Question reranking failed")
            
            # logger.info(f"Reranked results: {reranked_results}")

            final_docs = []
            for item in reranked_results:
                idx = item.get('index')
                relevance_score = item.get('relevance_score')
                if idx is None or relevance_score is None:
                    continue
                doc, _ = results[idx]
                doc.metadata['relevance_score'] = relevance_score
                if relevance_score > 0.15:  # Adjust this threshold as needed
                    final_docs.append(doc)

            # logger.info(f"Successfully retrieved and reranked {len(final_docs)} questions")
            return final_docs

    async def delete_question(self, question_id: str) -> dict:
        with db_manager.get_client() as client:
            if not client:
                raise Exception("Failed to connect to the database")

            collection = client.get_or_create_collection(self.collection_name)
            collection.delete(ids=[question_id])
            return {"message": "Question deleted successfully"}
        
    async def merge_questions(self, previous_question: str, new_question: str) -> str:
        prompt = f"""I will provide you with two similar questions. I am trying to build a knowledge base and repeating similar questions to store multiple times defeat the purpose.
Can you please create a new question/answer pair combining both. Please include all key informations from both of the question.
First: {previous_question}
Second: {new_question}
Please only respond with the only relevant information without missing any key context.
"""
        response = self.llm.invoke(prompt)
        # Extract the content from the response
        if isinstance(response.content, str):
            return response.content
        elif isinstance(response.content, list):
            # If it's a list, join all string elements
            return ", ".join([str(item) for item in response.content if isinstance(item, str)])
        else:
            # If it's neither a string nor a list, convert to string
            return str(response.content)