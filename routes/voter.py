

import base64
import cv2
import numpy as np
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from deepface import DeepFace
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime

voter_bp = Blueprint("voter_bp", __name__)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["voting_system"]
voters_collection = db["voters"]
elections_collection = db["elections"]
votes_collection = db["votes"]
complaints_collection = db["complaints"]

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def decode_image(image_base64):
    """Convert Base64 image to OpenCV format"""
    try:
        image_base64 = image_base64.replace(" ", "+")
        data = image_base64.split(",")[1]
        data += "=" * (-len(data) % 4)
        image_data = base64.b64decode(data)
        np_arr = np.frombuffer(image_data, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print("Image decode error:", e)
        return None


def detect_face(image):
    """Detect a face in an image"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces[0] if len(faces) > 0 else None  # Return first detected face or None

def get_face_distance(emb1, emb2):
    """Calculates strict cosine distance between two embeddings."""
    emb1 = np.array(emb1)
    emb2 = np.array(emb2)
    if np.linalg.norm(emb1) == 0 or np.linalg.norm(emb2) == 0:
        return float('inf')
    return 1 - (np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))



@voter_bp.route("/", methods=["GET"])
def voter_home():
    return render_template("voter_home.html")


@voter_bp.route("/complaint", methods=["GET", "POST"])
def complaint():
    if "voter_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("voter_bp.login"))

    voter_id = ObjectId(session["voter_id"])
    voter = voters_collection.find_one({"_id": voter_id})
    if not voter:
        flash("Voter not found!", "danger")
        return redirect(url_for("voter_bp.login"))

    if request.method == "POST":
        subject = request.form.get("subject")
        message = request.form.get("message")
        
        if not subject or not message:
            flash("Subject and message are required.", "danger")
            return redirect(url_for("voter_bp.complaint"))

        complaint_data = {
            "voter_id": voter_id,
            "voter_name": voter.get("name"),
            "location": voter.get("location"),
            "subject": subject,
            "message": message,
            "status": "Pending",
            "timestamp": datetime.now()
        }
        
        complaints_collection.insert_one(complaint_data)
        flash("Your complaint has been submitted successfully.", "success")
        return redirect(url_for("voter_bp.complaint"))

    # Fetch user's complaints
    user_complaints = list(complaints_collection.find({"voter_id": voter_id}).sort("timestamp", -1))
    return render_template("voter_complaint.html", voter_name=voter.get("name"), complaints=user_complaints)


@voter_bp.route("/login", methods=["GET", "POST"])
def login():
    import random
    if request.method == "POST":
        captcha_answer = request.form.get("captcha")
        
        # DEBUG LOGGING to check what is going on
        with open("captcha_log.txt", "a") as f:
            f.write(f"Session captcha: {session.get('captcha_answer')} | User submitted: {captcha_answer}\n")
        
        if str(session.get("captcha_answer")).strip() != str(captcha_answer).strip():
            flash("Invalid Captcha! Please try again.", "danger")
            return redirect(url_for("voter_bp.login"))

        email = request.form.get("email")
        password = request.form.get("password")

        voter = voters_collection.find_one({"email": email})
        if not voter or not check_password_hash(voter["password"], password):
            flash("Invalid email or password!", "danger")
            return redirect(url_for("voter_bp.login"))

        face_data = request.form.get("face_data")
        if not face_data:
            flash("Biometric verification required. Please scan your face.", "danger")
            return redirect(url_for("voter_bp.login"))
            
        try:
            face_img = decode_image(face_data)
            if face_img is None:
                raise ValueError("Invalid face image")
            target_embedding = DeepFace.represent(
                img_path=face_img,
                model_name="Facenet",
                detector_backend="opencv",
                enforce_detection=True
            )[0]["embedding"]
            
            if "face_embedding" not in voter or not voter["face_embedding"]:
                flash("Voter has no biometric data registered. Please re-register.", "danger")
                return redirect(url_for("voter_bp.login"))
                
            distance = get_face_distance(voter["face_embedding"], target_embedding)
            
            if distance > 0.40:  # Stricter Cosine Distance threshold for Facenet
                flash("Biometric mismatch! Unrecognized identity.", "danger")
                return redirect(url_for("voter_bp.login"))
        except Exception as e:
            flash("Error processing biometric scan. Ensure proper lighting and try again.", "danger")
            return redirect(url_for("voter_bp.login"))

        from utils import send_otp_email
        otp = str(random.randint(100000, 999999))
        session["pending_voter_id"] = str(voter["_id"])
        session["pending_voter_name"] = voter["name"]
        session["otp"] = otp
        
        email_sent = send_otp_email(email, otp)
        if email_sent:
            flash("OTP Sent to your registered email!", "info")
        else:
            flash(f"OTP Sent! (For prototype testing, your OTP is: {otp})", "info")
        return redirect(url_for("voter_bp.verify_otp"))

    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    session["captcha_answer"] = num1 + num2
    captcha_text = f"What is {num1} + {num2}?"
    return render_template("voter_login.html", captcha_text=captcha_text)

@voter_bp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_voter_id" not in session:
        return redirect(url_for("voter_bp.login"))
        
    if request.method == "POST":
        user_otp = request.form.get("otp")
        
        if user_otp == session.get("otp"):
            # OTP matched! Promote pending session to active session
            session["voter_id"] = session.pop("pending_voter_id")
            session["voter_name"] = session.pop("pending_voter_name")
            session.pop("otp", None)
            
            flash(f"2FA Successful! Welcome, {session['voter_name']}.", "success")
            return redirect(url_for("voter_bp.dashboard"))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            
    return render_template("verify_otp.html")


@voter_bp.route("/login/face", methods=["POST"])
def face_login():
    try:
        data = request.get_json()
        face_data = data.get("face_data")

        if not face_data:
            return jsonify({"error": "Face data is required!"})

        face_img = decode_image(face_data)
       
        target_embedding = DeepFace.represent( img_path=face_img,
              model_name="Facenet",
         detector_backend="opencv",
         enforce_detection=True
         )[0]["embedding"]
       
        # Compare with stored embeddings
        best_match = None
        best_distance = float("inf")

        for user in voters_collection.find():
            if "face_embedding" not in user or not user["face_embedding"]:
                continue
            distance = get_face_distance(user["face_embedding"], target_embedding)

            if distance < best_distance and distance < 0.40:  # Lower distance means better match
                best_distance = distance
                best_match = user

        if best_match:
            session["voter_id"] = str(best_match["_id"])
            session["voter_name"] = best_match["name"]
            return jsonify({"message": f"Login successful! Welcome, {best_match['name']}.", "redirect": url_for("voter_bp.dashboard")})
        else:
            return jsonify({"error": "Face not recognized! Please try again."})

    except Exception as e:
        return jsonify({"error": str(e)})




@voter_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("voter_bp.voter_home"))



@voter_bp.route("/verify_face", methods=["POST"])
def verify_face():
    """Verify voter's face before allowing them to vote."""
    try:
        data = request.get_json()
        face_data = data.get("face_data")

        if not face_data:
            return jsonify({"success": False, "error": "Face data is required!"})

        face_img = decode_image(face_data)
        if face_img is None:
            return jsonify({"success": False, "error": "Invalid face image!"})
        

        target_embedding = DeepFace.represent( img_path=face_img,
    model_name="Facenet",
    detector_backend="opencv",
    enforce_detection=True
)[0]["embedding"]

        # Compare with stored voter embeddings
        voter_id = session.get("voter_id")
        if not voter_id:
            return jsonify({"success": False, "error": "User session expired! Please log in again."})

        voter = voters_collection.find_one({"_id": ObjectId(voter_id)})
        if not voter:
            return jsonify({"success": False, "error": "Voter not found!"})

        if "face_embedding" not in voter or not voter["face_embedding"]:
            return jsonify({"success": False, "error": "Voter has no biometric data!"})

        distance = get_face_distance(voter["face_embedding"], target_embedding)

        if distance < 0.40:  # Stricter Cosine threshold
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Face not recognized!"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@voter_bp.route('/vote/<election_id>', methods=['GET', 'POST'])
def vote(election_id):
    if "voter_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("voter_bp.login"))

    voter_id = ObjectId(session["voter_id"])
    voter = voters_collection.find_one({"_id": voter_id})

    if not voter:
        flash("Voter not found!", "danger")
        return redirect(url_for("voter_bp.dashboard"))

    # Check if voter is verified
    if not voter.get("verified", False):
        flash("You are not verified to vote. Please contact the administrator.", "danger")
        return redirect(url_for("voter_bp.dashboard"))

    election = elections_collection.find_one({"_id": ObjectId(election_id)})
    if not election:
        flash("Election not found!", "danger")
        return redirect(url_for("voter_bp.dashboard"))

    current_time = datetime.now()
    start_t = election.get("start_time")
    end_t = election.get("end_time")

    if isinstance(start_t, str):
        try:
            start_t = datetime.strptime(start_t, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            start_t = datetime.strptime(start_t, "%Y-%m-%d %H:%M")
    if isinstance(end_t, str):
        try:
            end_t = datetime.strptime(end_t, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            end_t = datetime.strptime(end_t, "%Y-%m-%d %H:%M")

    if not (start_t <= current_time <= end_t):
        flash("This election is not currently active.", "danger")
        return redirect(url_for("voter_bp.dashboard"))

    candidates = election.get("candidates", [])

    if request.method == "POST":
        face_data = request.form.get("face_data")
        selected_candidate = request.form.get("candidate")

        if not face_data or not selected_candidate:
            flash("Please select a candidate and verify your face.", "danger")
            return redirect(url_for("voter_bp.vote", election_id=election_id))

        # Face recognition verification
        face_img = decode_image(face_data)
        

        # Extract facial embeddings
        try:
            target_embedding = DeepFace.represent( img_path=face_img,
    model_name="Facenet",
    detector_backend="opencv",
    enforce_detection=True
)[0]["embedding"]
        except:
            flash("Face recognition failed! Try again.", "danger")
            return redirect(url_for("voter_bp.vote", election_id=election_id))

        # Compare with stored voter embedding
        if "face_embedding" not in voter or not voter["face_embedding"]:
            flash("Biometric data not found! Please register again.", "danger")
            return redirect(url_for("voter_bp.vote", election_id=election_id))
            
        distance = get_face_distance(voter["face_embedding"], target_embedding)

        if distance > 0.40:  # Stricter Cosine threshold
            flash("Face does not match! Voting failed.", "danger")
            return redirect(url_for("voter_bp.vote", election_id=election_id))

        # Check if voter has already voted
        existing_vote = votes_collection.find_one({"voter_id": voter_id, "election_id": ObjectId(election_id)})
        if existing_vote:
            flash("You have already voted in this election!", "warning")
            return redirect(url_for("voter_bp.dashboard"))

        # Store vote in database
        import hashlib
        from db import encrypt_vote
        
        # Generate Cryptographic Vote Receipt Hash
        receipt_string = f"{voter_id}-{election_id}-{datetime.now().isoformat()}"
        vote_hash = hashlib.sha256(receipt_string.encode()).hexdigest()
        
        # Encrypt the vote choice
        encrypted_candidate = encrypt_vote(selected_candidate)
        
        vote_data = {
            "voter_id": voter_id,
            "election_id": ObjectId(election_id),
            "candidate": encrypted_candidate,
            "timestamp": datetime.now(),
            "receipt_hash": vote_hash
        }
        votes_collection.insert_one(vote_data)

        flash("You have successfully voted! Cryptographic receipt generated.", "success")
        return redirect(url_for("voter_bp.vote_success", hash=vote_hash))

    return render_template("vote.html", election=election, candidates=candidates)

@voter_bp.route('/vote_success/<hash>')
def vote_success(hash):
    if "voter_id" not in session:
        return redirect(url_for("voter_bp.login"))
    return render_template("vote_success.html", receipt_hash=hash)







   



from ast import literal_eval
@voter_bp.route("/election_results/<election_id>", methods=["GET"])
def voter_election_results(election_id):
    if "voter_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("voter_bp.login"))

    voter_id = ObjectId(session["voter_id"])
    voter = voters_collection.find_one({"_id": voter_id})

    if not voter:
        flash("Voter not found!", "danger")
        return redirect(url_for("voter_bp.dashboard"))

    # Fetch the election
    election = elections_collection.find_one({"_id": ObjectId(election_id)})
    if not election:
        flash("Election not found!", "danger")
        return redirect(url_for("voter_bp.dashboard"))

    # Check if the voter's location matches the election's region
    if election.get("region") != voter.get("location"):
        flash("You are not eligible to view results for this election.", "danger")
        return redirect(url_for("voter_bp.dashboard"))

    # Fetch all votes for the election
    votes = list(votes_collection.find({"election_id": ObjectId(election_id)}))

    # Aggregate votes manually
    from db import decrypt_vote
    results = {}
    for vote in votes:
        # Decrypt the candidate string, then parse it into a dictionary
        try:
            raw_candidate = decrypt_vote(vote["candidate"])
            candidate = literal_eval(raw_candidate)  # Convert string to dictionary
            candidate_key = (candidate["name"], candidate["party"])  # Use (name, party) as key
        except (ValueError, KeyError, SyntaxError):
            continue  # Skip invalid candidate data

        # Count votes for each candidate
        if candidate_key in results:
            results[candidate_key] += 1
        else:
            results[candidate_key] = 1

    # Convert results to a list of dictionaries for the template
    results_list = [
        {"candidate": key[0], "party": key[1], "votes": value}
        for key, value in results.items()
    ]

    # Sort results by vote count (descending)
    results_list.sort(key=lambda x: x["votes"], reverse=True)

    return render_template("voter_election_results.html", election=election, results=results_list)












import base64
import numpy as np
from flask import request, flash, redirect, url_for, render_template
from werkzeug.security import generate_password_hash
from deepface import DeepFace
import cv2
import json
from bson.binary import Binary

@voter_bp.route("/register", methods=["GET", "POST"])
def register():
    import random
    from datetime import datetime

    if request.method == "POST":

        # CAPTCHA
        captcha_answer = request.form.get("captcha")
        if str(session.get("captcha_answer")) != str(captcha_answer):
            flash("Invalid Captcha! Please try again.", "danger")
            return redirect(url_for("voter_bp.register"))

        # FORM DATA
        name = request.form.get("name")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        location = request.form.get("location").strip().lower()    
        face_data = request.form.get("face_data")
        Voter_Id = request.form.get("Voter_Id")
        if not Voter_Id or not Voter_Id.strip():
            import string
            import random
            Voter_Id = "SYS-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        Mobile_Num = request.form.get("mobile_num")
        dob = request.form.get("dob")
        age = int(request.form.get("age", 0))
        Aadhar_Id = request.form.get("Aadhar_Id")

        # 🔥 DOB VALIDATION
        dob_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()

        calculated_age = today.year - dob_date.year - (
            (today.month, today.day) < (dob_date.month, dob_date.day)
        )

        if age != calculated_age:
            flash("Age does not match Date of Birth!", "danger")
            return redirect(url_for("voter_bp.register"))

        if calculated_age < 18:
            flash("You must be 18+ to register!", "danger")
            return redirect(url_for("voter_bp.register"))

        # Aadhaar validation
        if not Aadhar_Id or not Aadhar_Id.isdigit() or len(Aadhar_Id) != 12:
            flash("Aadhaar ID must be exactly 12 digits.", "danger")
            return redirect(url_for("voter_bp.register"))

        if voters_collection.find_one({"Aadhar_Id": Aadhar_Id}):
            flash("Aadhaar already registered!", "danger")
            return redirect(url_for("voter_bp.register"))

        # FACE CHECK
        if not face_data:
            flash("Please capture your face!", "danger")
            return redirect(url_for("voter_bp.register"))

        face_data = face_data.replace(" ", "+")
        try:
            b64_str = face_data.split(",")[1]
            b64_str += "=" * (-len(b64_str) % 4)
            face_img_data = base64.b64decode(b64_str)
        except:
            flash("Invalid image format!", "danger")
            return redirect(url_for("voter_bp.register"))

        np_arr = np.frombuffer(face_img_data, np.uint8)
        face_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        

        try:
           embedding = DeepFace.represent(
          img_path=face_img,
          model_name="Facenet",
          detector_backend="opencv",
          enforce_detection=True
            )[0]["embedding"]     
        except:
            flash("Face recognition failed!", "danger")
            return redirect(url_for("voter_bp.register"))

        # SAVE DATA
        voter_data = {
            "name": name,
            "email": email,
            "password": password,
            "face_embedding": embedding,
            "location": location,
            "Voter_Id": Voter_Id,
            "Aadhar_Id": Aadhar_Id,
            "Mobile_Num": Mobile_Num,
            "dob": dob,
            "age": calculated_age,
            "verified": False,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "face_image": Binary(face_img_data)
        }

        voters_collection.insert_one(voter_data)

        flash("Registration successful!", "success")
        return redirect(url_for("voter_bp.voter_home"))

    # CAPTCHA GENERATE
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    session["captcha_answer"] = num1 + num2
    captcha_text = f"What is {num1} + {num2}?"

    return render_template("voter_register.html", captcha_text=captcha_text)




import base64
from flask import session, flash, redirect, url_for, render_template
from bson.objectid import ObjectId
from datetime import datetime

@voter_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if "voter_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("voter_bp.login"))

    voter_id = ObjectId(session["voter_id"])
    current_time = datetime.now()

    # Fetch voter details including location, verification status, and face image
    voter = voters_collection.find_one({"_id": voter_id}, {"name": 1, "location": 1, "verified": 1, "face_image": 1})
    if not voter:
        flash("Voter not found!", "danger")
        return redirect(url_for("voter_bp.login"))

    voter_name = voter.get("name", "Voter")  # Default to "Voter" if name is missing
    voter_location = voter.get("location", "").strip().lower()   
    print("👉 Voter location:", voter_location)
    print("👉 All election regions:", list(elections_collection.find({}, {"region": 1})))
    voter_verified = voter.get("verified", False)  # Get the voter's verification status
    face_image_data = voter.get("face_image")  # Retrieve binary image data

    if not voter_location:
        flash("Your location is not set. Please update your profile.", "warning")
        return redirect(url_for("voter_bp.voter_home"))

    # Convert binary image to Base64 for rendering in HTML
    face_image_base64 = None
    if face_image_data:
        face_image_base64 = base64.b64encode(face_image_data).decode("utf-8")

    # Fetch all elections
    all_elections = list(elections_collection.find())

    ongoing_elections = []
    upcoming_elections = []
    other_region_elections = []
    
    for election in all_elections:
        start_t = election.get("start_time")
        end_t = election.get("end_time")
        
        if isinstance(start_t, str):
            try:
                start_t = datetime.strptime(start_t, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                start_t = datetime.strptime(start_t, "%Y-%m-%d %H:%M")
        if isinstance(end_t, str):
            try:
                end_t = datetime.strptime(end_t, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                end_t = datetime.strptime(end_t, "%Y-%m-%d %H:%M")

        is_voter_region = (election.get("region", "").strip().lower() == voter_location)

        if start_t <= current_time <= end_t:
            if is_voter_region:
                ongoing_elections.append(election)
            else:
                other_region_elections.append(election)
        elif current_time < start_t:
            if is_voter_region:
                upcoming_elections.append(election)

    # Fetch voted elections
    voted_elections = votes_collection.find({"voter_id": voter_id})
    voted_election_ids = {str(vote["election_id"]) for vote in voted_elections}

    return render_template(
        "voter_dashboard.html",
        voter_name=voter_name,  
        voter=voter,
        voter_location=voter.get("location", "").title(),
        face_image=face_image_base64,  # Pass face image to template
        ongoing_elections=ongoing_elections,
        upcoming_elections=upcoming_elections,
        other_region_elections=other_region_elections,
        voted_election_ids=voted_election_ids
    )
