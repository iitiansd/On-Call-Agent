# app/services/vector_db.py

from app.core.db import db_manager
from langchain.schema import Document
from typing import List
import uuid
import os
from app.core.config import settings
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from app.core.logging_config import logging

# logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self):
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        self.collection_name = "documents"
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_document")

    async def insert_documents(self, documents: List[Document]):
        with db_manager.get_client() as client:
            if not client:
                raise Exception("Failed to connect to the database")
            
            vector_store = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )

            uuids = [str(uuid.uuid4()) for _ in range(len(documents))]

            # print(documents[0], uuids[0])

            vector_store.add_documents(documents=documents, ids=uuids)

    async def search_documents(self, organization_id: str, query: str, k: int = 10):
        with db_manager.get_client() as client:
            if not client:
                raise Exception("Failed to connect to the database")

            vector_store = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )

            # print(vector_store)

            results = vector_store.similarity_search_with_score(
                query,
                k=k
            )

            # Convert results to Document objects
            documents = [
                Document(page_content=doc.page_content, metadata=doc.metadata) for doc, _ in results
            ]

            # logger.info(f"Retrieved {len(documents)} documents from vector store")
            return documents


    async def delete_documents(self, organization_id: str, source_document_id: str):
        with db_manager.get_client() as client:
            if not client:
                raise Exception("failed to connect to the database")
            
            collection = client.get_or_create_collection(self.collection_name)
            collection.delete(
                where={"source_document_id": source_document_id}
            )
            return {"message": "Documents deleted successfully"}