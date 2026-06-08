from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["voting_system"]

voter_location = "madhya pradesh"
all_elections = list(db.elections.find({
   "region": {"$regex": f"^{voter_location}$", "$options": "i"}
}))
print("Found elections:", all_elections)
