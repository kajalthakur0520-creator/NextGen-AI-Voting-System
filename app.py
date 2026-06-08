from flask import Flask, render_template
from db import mongo  # Import MongoDB instance from db.py
from routes.admin import admin_bp
from routes.voter import voter_bp
from routes.candidate import candidate_bp

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/voting_system"
app.config["SECRET_KEY"] = "your_super_secret_key"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB limit for large face images
app.config["MAX_FORM_MEMORY_SIZE"] = 50 * 1024 * 1024  # Needed for Werkzeug 3.0+ for large form fields
mongo.init_app(app)  # Initialize MongoDB with the Flask app

# Register Blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(voter_bp, url_prefix="/voter")
app.register_blueprint(candidate_bp, url_prefix="/candidate")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)


