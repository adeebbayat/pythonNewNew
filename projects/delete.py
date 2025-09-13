from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://adeebbayat:1onXjDE0WCwXfvhY@cluster0.cki8y81.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


client = MongoClient(uri, server_api=ServerApi('1'))
db = client["testdb"]          # pick a database
collection = db["price"]       # pick a collection



collection.delete_many({})
print("All documents deleted!")
