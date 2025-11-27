# ./information-generation/app/core/db.py

from chromadb import HttpClient
from app.core.config import settings
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __init__(self):
        self.client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    def connect(self):
        if self.client is None:
            try:
                self.client = HttpClient(host=settings.CHROME_DB_URI)
                logger.info("Connected to ChromeDB")
            except Exception as e:
                logger.error(f"Failed to connect to ChromeDB: {str(e)}")
                raise

    def disconnect(self):
        if self.client:
            self.client = None
            logger.info("Disconnected from ChromeDB")

    @contextmanager
    def get_client(self):
        self.connect()
        try:
            yield self.client
        finally:
            self.disconnect()

db_manager = DatabaseManager.get_instance()