# mongo_client.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class MongoDBClient:
    def __init__(self, uri="mongodb+srv://hackathon6sense:hackathon6sense@hackathon.m2osc.mongodb.net/?retryWrites=true&w=majority&appName=Hackathon", db_name="hackathon", collection_name="chatHistory"):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        try:
            # Create a new client and connect to the server
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Send a ping to confirm a successful connection
            # self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print("Failed to connect to MongoDB:", e)
    
    def get_collection(self):
        if self.collection is None:
            self.connect()
        return self.collection
