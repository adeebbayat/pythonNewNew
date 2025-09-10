from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://adeebbayat:1onXjDE0WCwXfvhY@cluster0.cki8y81.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    db = client["testdb"]          # pick a database
    collection = db["price"]       # pick a collection

    examplePrice = {"value":200}   # your example data

    #  get lowest price BEFORE inserting
    old_lowest_doc = collection.find_one(sort=[("value", 1)])
    old_lowest = old_lowest_doc["value"] if old_lowest_doc else None

    collection.insert_one(examplePrice)     # insert into MongoDB
    print("Inserted one price!")

except Exception as e:
    print(e)

#  only build array AFTER insert if you want to see all
array = []
for item in collection.find():
    array.append(item['value'])

array.sort()
print(array)

#  compare new entry with old lowest
if old_lowest is not None:
    diff_percent = ((examplePrice["value"] - old_lowest) / old_lowest) * 100
    diff_percent = round(diff_percent, 2)

    if examplePrice["value"] < old_lowest:
        print(f"The new price {examplePrice['value']} is {abs(diff_percent)}% LOWER than the old lowest {old_lowest}")
    elif examplePrice["value"] > old_lowest:
        print(f"The new price {examplePrice['value']} is {diff_percent}% HIGHER than the old lowest {old_lowest}")
    else:
        print(f"The new price {examplePrice['value']} is the SAME as the old lowest {old_lowest}")
else:
    print("This is the first price in the collection.")

collection.delete_many({})
print("All documents deleted!")
