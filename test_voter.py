import requests

# Try fetching via app (simulating the query without login is hard, but we can call the function)
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["voting_system"]

voter = db.voters.find_one()
voter_location = voter.get("location", "").strip().lower()

all_elections = list(db.elections.find({
   "region": {"$regex": f"^{voter_location}$", "$options": "i"}
}))

print("Voter location:", voter_location)
print("All elections matched:", [e["name"] for e in all_elections])

import datetime
current_time = datetime.datetime.now()

ongoing = []
upcoming = []
for election in all_elections:
    start_t = election.get("start_time")
    end_t = election.get("end_time")
    if start_t <= current_time <= end_t:
        ongoing.append(election)
    elif current_time < start_t:
        upcoming.append(election)

print("Ongoing:", [e["name"] for e in ongoing])
print("Upcoming:", [e["name"] for e in upcoming])
