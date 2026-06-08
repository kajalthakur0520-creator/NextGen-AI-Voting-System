from flask import Blueprint, render_template, request, redirect, session, jsonify, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils import send_otp_email
import random
from bson.objectid import ObjectId
from datetime import datetime
import base64
import cv2  # Just in case we need face processing for candidates too
import numpy as np

# from app import mongo # Avoid circular import, better to use pymongo direct or db.py
from db import mongo

candidate_bp = Blueprint("candidate_bp", __name__)

@candidate_bp.route("/")
def candidate_home():
    return redirect(url_for("candidate_bp.login"))

@candidate_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        candidate = mongo.db.candidates.find_one({"email": email})
        if not candidate or not check_password_hash(candidate["password"], password):
            flash("Invalid email or password!", "danger")
            return redirect(url_for("candidate_bp.login"))

        otp = str(random.randint(100000, 999999))
        session["pending_candidate_id"] = str(candidate["_id"])
        session["pending_candidate_name"] = candidate["name"]
        session["candidate_otp"] = otp
        
        email_sent = send_otp_email(email, otp)
        if email_sent:
            flash("OTP Sent to your registered email!", "info")
        else:
            flash(f"OTP Sent! (For prototype testing, your OTP is: {otp})", "info")
            
        return redirect(url_for("candidate_bp.verify_otp"))

    return render_template("candidate_login.html")

@candidate_bp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_candidate_id" not in session:
        return redirect(url_for("candidate_bp.login"))
        
    if request.method == "POST":
        user_otp = request.form.get("otp")
        
        if user_otp == session.get("candidate_otp"):
            session["candidate_id"] = session.pop("pending_candidate_id")
            session["candidate_name"] = session.pop("pending_candidate_name")
            session.pop("candidate_otp", None)
            
            flash(f"2FA Successful! Welcome, {session['candidate_name']}.", "success")
            return redirect(url_for("candidate_bp.dashboard"))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            
    return render_template("verify_otp.html", target_url=url_for("candidate_bp.verify_otp"))

@candidate_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        party = request.form.get("party")
        manifesto = request.form.get("manifesto")
        region = request.form.get("region")
        election_type = request.form.get("election_type")
        
        logo_base64 = None
        if "logo" in request.files:
            file = request.files["logo"]
            if file and file.filename != "":
                import base64
                logo_base64 = "data:" + file.content_type + ";base64," + base64.b64encode(file.read()).decode("utf-8")
        
        # Check if email already exists
        if mongo.db.candidates.find_one({"email": email}):
            flash("Email already registered!", "danger")
            return redirect(url_for("candidate_bp.register"))
            
        candidate_data = {
            "name": name,
            "email": email,
            "password": password,
            "party": party,
            "region": region,
            "election_type": election_type,
            "manifesto": manifesto,
            "logo": logo_base64,
            "approved": False,
            "registration_date": datetime.now()
        }
        
        mongo.db.candidates.insert_one(candidate_data)
        flash("Application submitted! Awaiting admin approval.", "success")
        return redirect(url_for("candidate_bp.login"))

    return render_template("candidate_register.html")

@candidate_bp.route("/dashboard")
def dashboard():
    if "candidate_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("candidate_bp.login"))

    candidate_id = ObjectId(session["candidate_id"])
    candidate = mongo.db.candidates.find_one({"_id": candidate_id})
    
    if not candidate:
        session.pop("candidate_id", None)
        return redirect(url_for("candidate_bp.login"))

    return render_template("candidate_dashboard.html", candidate=candidate)

@candidate_bp.route("/logout")
def logout():
    session.pop("candidate_id", None)
    session.pop("candidate_name", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("candidate_bp.login"))
