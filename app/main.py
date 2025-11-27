# In app/main.py or a similar central module
from app.scripts.connection_manager import ConnectionManager
manager = ConnectionManager()

# In your other files, import the shared `manager` instance

