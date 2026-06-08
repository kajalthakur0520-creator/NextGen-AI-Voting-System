from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["voting_system"]

voters = list(db.voters.find({}, {"name": 1, "location": 1}))
elections = list(db.elections.find({}))

print("Voters:", voters)
for e in elections:
    print("Election:", e["name"], "Region:", e.get("region"), "Start:", e.get("start_time"), "End:", e.get("end_time"))
