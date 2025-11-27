pip install -r requirements.txt

run chromadb locally:
 pip install chromadb
 chroma run --path ./vector_database --port 8123

to run fast app
    uvicorn app.scripts.manage_document_flow:app --reload --port 8003

To upload a document:
python3 app/scripts/manage_document_flow.py upload enghestia.pdf org_123

python app/scripts/manage_document_flow.py upload enghestia.pdf org_123


To chat with the system:
python app/scripts/manage_document_flow.py chat "What Hestia Deployer provides features?" "org_123"

python app/scripts/manage_document_flow.py chat "What is AI?" "org_123"


To add a question-answer pair:
python app/scripts/manage_document_flow.py question "What is AI?" "Artificial Intelligence is a branch of computer science." "org_123"

python app/scripts/manage_document_flow.py question "What is llm integration?" "6sense hackathon team Uses OpenAI/Google API, fetching context from the knowledge base." "org_123"



python -m pip install "pymongo[srv]"


python3 app/mongodb.py              
Pinged your deployment. You successfully connected to MongoDB!





installation 
pip install weaviate-client
pip install lark
pip install slack_sdk
