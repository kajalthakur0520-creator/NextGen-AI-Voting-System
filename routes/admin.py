from flask import Blueprint, render_template, request, redirect, session, jsonify, url_for, flash
from datetime import datetime
from bson.objectid import ObjectId
# from app import mongo
from db import mongo
from ast import literal_eval

admin_bp = Blueprint("admin_bp", __name__)

# Hardcoded Admin Credentials
ADMIN_EMAIL = "admin@123"
ADMIN_PASSWORD = "admin"

# ✅ Admin Login Page
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # 👉 DB से admin fetch करो
        admin = mongo.db.admins.find_one({"email": email})

        if admin and admin["password"] == password:

            import random
            from utils import send_otp_email

            otp = str(random.randint(100000, 999999))

            # ✅ correct session
            session["admin_pending_id"] = str(admin["_id"])
            session["admin_otp"] = otp

            send_otp_email(admin["email"], otp)

            flash("OTP sent to your email!", "info")
            return redirect(url_for("admin_bp.verify_otp"))

        else:
            flash("Invalid Credentials", "danger")

    return render_template("admin_login.html")



@admin_bp.route("/verify_otp", methods=["GET", "POST"])
@admin_bp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "admin_pending_id" not in session:
        return redirect(url_for("admin_bp.login"))

    if request.method == "POST":
        user_otp = request.form.get("otp")

        if user_otp == session.get("admin_otp"):
            session["admin_logged_in"] = True

            session.pop("admin_pending_id", None)
            session.pop("admin_otp", None)

            flash("Login Successful!", "success")
            return redirect(url_for("admin_bp.dashboard"))
        else:
            flash("Invalid OTP", "danger")

    return render_template("admin_verify_otp.html")

@admin_bp.route("/dashboard")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    elections = mongo.db.elections.find()
    
    now = datetime.now()

    # Categorize elections
    ongoing = []
    upcoming = []
    completed = []

    for election in elections:
        start_time = election["start_time"]
        end_time = election["end_time"]

        # Ensure datetime format
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        # Categorize elections
        if start_time <= now <= end_time:
            ongoing.append(election)
        elif now < start_time:
            upcoming.append(election)
        else:
            completed.append(election)

    # Calculate Turnout Metrics
    total_registered = mongo.db.voters.count_documents({})
    total_verified = mongo.db.voters.count_documents({"verified": True})
    
    # Calculate total votes cast across all elections (overall system turnout)
    total_votes_cast = mongo.db.votes.count_documents({})
    
    turnout_percentage = 0
    if total_verified > 0:
        turnout_percentage = round((total_votes_cast / total_verified) * 100, 1)

    # Fetch Pending Candidates
    pending_candidates = list(mongo.db.candidates.find({"approved": False}))
    total_pending_candidates = len(pending_candidates)
    total_verified_candidates = mongo.db.candidates.count_documents({"approved": True})
    
    # Complaints Metric
    pending_complaints_count = mongo.db.complaints.count_documents({"status": "Pending"})

    return render_template(
        "admin_dashboard.html", 
        ongoing=ongoing, 
        upcoming=upcoming, 
        completed=completed,
        total_registered=total_registered,
        total_verified=total_verified,
        total_votes_cast=total_votes_cast,
        turnout_percentage=turnout_percentage,
        pending_candidates=pending_candidates,
        total_pending_candidates=total_pending_candidates,
        total_verified_candidates=total_verified_candidates,
        pending_complaints_count=pending_complaints_count
    )

# ✅ Admin Logout
@admin_bp.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")

# ✅ Route to Create a New Election
@admin_bp.route("/create_election", methods=["GET", "POST"])
def create_election():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    if request.method == "POST":
        from app import mongo  # Import here to avoid circular import

        name = request.form["name"]
        region = request.form.get("region").strip().lower()        
        election_type = request.form.get("election_type", "General Election (Lok Sabha)")
        start_time = request.form["start_time"].replace("T", " ")
        end_time = request.form["end_time"].replace("T", " ")

        try:
             start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
             end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
        except ValueError as e:
             print("Date Error:", e)
             return "Invalid date format", 400

        election_data = {
            "name": name,
            "region": region,
            "type": election_type,
            "start_time": start_time,
            "end_time": end_time,
            "candidates": []
        }

        mongo.db.elections.insert_one(election_data)
        
        # Add to Audit Log
        mongo.db.audit_logs.insert_one({
            "action": "Created Election",
            "details": f"Election '{name}' for region '{region}' starting at {start_time}",
            "timestamp": datetime.now()
        })
        
        return redirect("/admin/dashboard")

    return render_template("create_election.html")

# ✅ Route to Add Candidates to an Election
@admin_bp.route("/add_candidate/<election_id>", methods=["GET", "POST"])
def add_candidate(election_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    if request.method == "POST":
        candidate_type = request.form.get("candidate_type", "custom")
        
        if candidate_type == "existing":
            candidate_id = request.form.get("existing_candidate_id")
            if not candidate_id:
                flash("Please select a candidate.", "danger")
                return redirect(url_for("admin_bp.add_candidate", election_id=election_id))
            
            existing_candidate = mongo.db.candidates.find_one({"_id": ObjectId(candidate_id)})
            if not existing_candidate:
                flash("Candidate not found.", "danger")
                return redirect(url_for("admin_bp.add_candidate", election_id=election_id))
                
            candidate_data = {
                "name": existing_candidate["name"],
                "party": existing_candidate["party"],
                "description": existing_candidate.get("manifesto", "")
            }
            if "logo" in existing_candidate and existing_candidate["logo"]:
                candidate_data["logo"] = existing_candidate["logo"]
                
        else:
            candidate_name = request.form["name"]
            candidate_party = request.form["party"]
            description = request.form.get("description", "")
            
            logo_base64 = None
            if "logo" in request.files:
                file = request.files["logo"]
                if file and file.filename != "":
                    import base64
                    logo_base64 = "data:" + file.content_type + ";base64," + base64.b64encode(file.read()).decode("utf-8")
            
            candidate_data = {
                "name": candidate_name, 
                "party": candidate_party, 
                "description": description
            }
            if logo_base64:
                candidate_data["logo"] = logo_base64
            
        mongo.db.elections.update_one(
            {"_id": ObjectId(election_id)},
            {"$push": {"candidates": candidate_data}}
         )

        # Add to Audit Log
        mongo.db.audit_logs.insert_one({
            "action": "Added Candidate",
            "details": f"Added {candidate_data['name']} ({candidate_data['party']}) to Election ID: {election_id}",
            "timestamp": datetime.now()
        })

        return redirect("/admin/dashboard")

    verified_candidates = list(mongo.db.candidates.find({"approved": True}))
    return render_template("add_candidate.html", election_id=election_id, verified_candidates=verified_candidates)





@admin_bp.route("/delete_candidate/<election_id>/<candidate_name>/<candidate_party>")
def delete_candidate(election_id, candidate_name, candidate_party):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    # Remove candidate by matching name and party
    mongo.db.elections.update_one(
        {"_id": ObjectId(election_id)},
        {"$pull": {"candidates": {"name": candidate_name, "party": candidate_party}}}
    )

    # Add to Audit Log
    mongo.db.audit_logs.insert_one({
        "action": "Removed Candidate",
        "details": f"Removed {candidate_name} ({candidate_party}) from Election ID: {election_id}",
        "timestamp": datetime.now()
    })

    # flash("Candidate deleted successfully!", "success")
    return redirect(url_for("admin_bp.dashboard"))


@admin_bp.route("/verified_voters")
def verified_voters():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    # Fetch verified voters (verified: True)
    verified_voters = list(mongo.db.voters.find({"verified": True}))

    return render_template("verified_voters.html", voters=verified_voters)

@admin_bp.route("/registered_voters")
def registered_voters():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    # Fetch unverified voters (verified: False)
    unverified_voters = list(mongo.db.voters.find({"verified": False}))

    return render_template("pending_voters.html", voters=unverified_voters)

@admin_bp.route("/verified_candidates")
def verified_candidates():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    verified_candidates = list(mongo.db.candidates.find({"approved": True}))
    return render_template("verified_candidates.html", candidates=verified_candidates)

@admin_bp.route("/pending_candidates")
def pending_candidates():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    pending_candidates = list(mongo.db.candidates.find({"approved": False}))
    return render_template("pending_candidates.html", candidates=pending_candidates)


@admin_bp.route("/approve_voter/<voter_id>", methods=["POST"])
def approve_voter(voter_id):
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    # Update voter status to verified (True)
    mongo.db.voters.update_one({"_id": ObjectId(voter_id)}, {"$set": {"verified": True}})

    # Add to Audit Log
    mongo.db.audit_logs.insert_one({
        "action": "Verified Voter",
        "details": f"Approved Voter ID: {voter_id}",
        "timestamp": datetime.now()
    })

    return jsonify({"message": "Voter Verified Successfully"}), 200






@admin_bp.route("/delete_election/<election_id>", methods=["POST"])
def delete_election(election_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    try:
        # Delete the election by ID
        result = mongo.db.elections.delete_one({"_id": ObjectId(election_id)})

        if result.deleted_count > 0:
            # Add to Audit Log
            mongo.db.audit_logs.insert_one({
                "action": "Deleted Election",
                "details": f"Permanently deleted Election ID: {election_id}",
                "timestamp": datetime.now()
            })
            return redirect(url_for("admin_bp.dashboard"))
        else:
            return "Election not found", 404

    except Exception as e:
        return str(e), 500

@admin_bp.route("/approve_candidate/<candidate_id>", methods=["POST"])
def approve_candidate(candidate_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))
    
    mongo.db.candidates.update_one({"_id": ObjectId(candidate_id)}, {"$set": {"approved": True}})
    mongo.db.audit_logs.insert_one({
        "action": "Approved Candidate",
        "details": f"Approved Candidate ID: {candidate_id}",
        "timestamp": datetime.now()
    })
    flash("Candidate approved successfully.", "success")
    return redirect(url_for("admin_bp.dashboard"))

@admin_bp.route("/reject_candidate/<candidate_id>", methods=["POST"])
def reject_candidate(candidate_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))
        
    mongo.db.candidates.delete_one({"_id": ObjectId(candidate_id)})
    mongo.db.audit_logs.insert_one({
        "action": "Rejected Candidate",
        "details": f"Rejected and removed Candidate ID: {candidate_id}",
        "timestamp": datetime.now()
    })
    flash("Candidate rejected.", "info")
    return redirect(url_for("admin_bp.dashboard"))













@admin_bp.route('/election_results/<election_id>')
def election_results(election_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    election_id = ObjectId(election_id)  # Convert to ObjectId for MongoDB lookup

    # Fetch votes for the given election
    votes = list(mongo.db.votes.find({"election_id": election_id}))

    # Count votes per candidate
    from db import decrypt_vote
    vote_count = {}
    for vote in votes:
        candidate_data = decrypt_vote(vote.get("candidate"))

        # If candidate_data is a dictionary (as a string), convert it back
        if isinstance(candidate_data, str) and candidate_data.startswith("{"):
            candidate_data = eval(candidate_data)  # Convert string to dictionary (or use `json.loads` safely)

        if isinstance(candidate_data, dict):
            candidate_name = candidate_data.get("name", "Unknown")
            candidate_party = candidate_data.get("party", "Independent")
        else:
            candidate_name = candidate_data
            candidate_party = "Independent"  # Default party if not stored

        key = (candidate_name, candidate_party)  # Tuple key (name, party)
        vote_count[key] = vote_count.get(key, 0) + 1  # Count votes

    # Convert data into a list format for Jinja2 (using "candidate" instead of "name" to match JS)
    results = [{"candidate": k[0], "party": k[1], "votes": v} for k, v in vote_count.items()]
    total_votes = sum(r["votes"] for r in results)

    # Fetch election details (optional)
    election = mongo.db.elections.find_one({"_id": election_id})

    # Check if election is ended and calculate winner
    is_ended = False
    winners = []
    if election:
        end_time = election.get("end_time")
        if isinstance(end_time, datetime):
            if datetime.now() > end_time:
                is_ended = True
        elif isinstance(end_time, str):
            try:
                dt_obj = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > dt_obj:
                    is_ended = True
            except ValueError:
                try:
                    dt_obj = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
                    if datetime.now() > dt_obj:
                        is_ended = True
                except ValueError:
                    pass
        
    if is_ended and results:
        max_votes = max(results, key=lambda x: x["votes"])["votes"]
        if max_votes > 0:
            winners = [r for r in results if r["votes"] == max_votes]

    return render_template("election_results.html", results=results, election=election, total_votes=total_votes, is_ended=is_ended, winners=winners)




@admin_bp.route("/complaints")
def manage_complaints():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    # Fetch all complaints, newest first
    complaints = list(mongo.db.complaints.find().sort("timestamp", -1))
    return render_template("admin_complaints.html", complaints=complaints)

@admin_bp.route("/resolve_complaint/<complaint_id>", methods=["POST"])
def resolve_complaint(complaint_id):
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        mongo.db.complaints.update_one(
            {"_id": ObjectId(complaint_id)}, 
            {"$set": {"status": "Resolved"}}
        )

        mongo.db.audit_logs.insert_one({
            "action": "Resolved Complaint",
            "details": f"Marked Complaint ID: {complaint_id} as Resolved",
            "timestamp": datetime.now()
        })
        
        # It's better to reload page smoothly
        return redirect(url_for("admin_bp.manage_complaints"))
    except Exception as e:
        return str(e), 500


@admin_bp.route("/audit_logs")
def audit_logs():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.login"))

    # Fetch logs sorted by newest first
    logs = list(mongo.db.audit_logs.find().sort("timestamp", -1).limit(100))
    return render_template("admin_audit.html", logs=logs)

@admin_bp.route("/deny_verification/<voter_id>", methods=["POST"])
def deny_verification(voter_id):
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Delete the voter from the database
        result = mongo.db.voters.delete_one({"_id": ObjectId(voter_id)})
        if result.deleted_count > 0:
            # Add to Audit Log
            mongo.db.audit_logs.insert_one({
                "action": "Denied Voter",
                "details": f"Rejected & Removed Voter ID: {voter_id}",
                "timestamp": datetime.now()
            })
            return jsonify({"message": "Voter denied and removed successfully!"}), 200
        else:
            return jsonify({"error": "Voter not found!"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500