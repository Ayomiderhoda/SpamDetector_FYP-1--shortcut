from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import joblib, os, re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "spam_fyp_secret_2026"

BASE = os.path.dirname(os.path.abspath(__file__))
model      = joblib.load(os.path.join(BASE, "spam_model.pkl"))
vectorizer = joblib.load(os.path.join(BASE, "vectorizer.pkl"))

# Simple in-memory stores (fine for FYP demo)
USERS   = {"demo@gmail.com": {"name": "Ayomide Jacob", "password": "demo123"}}
HISTORY = {"demo@gmail.com": []}

# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        pw    = request.form.get("password", "").strip()
        if email in USERS and USERS[email]["password"] == pw:
            session["email"] = email
            session["name"]  = USERS[email]["name"]
            return redirect(url_for("dashboard"))
        error = "Wrong email or password. Try demo@gmail.com / demo123"
    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = ""
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        pw      = request.form.get("password", "").strip()
        confirm = request.form.get("confirm", "").strip()
        if not name or not email or not pw:
            error = "All fields are required."
        elif pw != confirm:
            error = "Passwords do not match."
        elif email in USERS:
            error = "Account already exists. Please login."
        else:
            USERS[email]   = {"name": name, "password": pw}
            HISTORY[email] = []
            session["email"] = email
            session["name"]  = name
            return redirect(url_for("dashboard"))
    return render_template("signup.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))
    h     = HISTORY.get(session["email"], [])
    spam  = sum(1 for x in h if x["result"] == "Spam")
    return render_template("dashboard.html",
        name=session["name"], total=len(h), spam=spam, safe=len(h)-spam)

@app.route("/detect")
def detect():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("detect.html", name=session["name"])

@app.route("/history")
def history():
    if "email" not in session:
        return redirect(url_for("login"))
    records = list(reversed(HISTORY.get(session["email"], [])))
    return render_template("history.html", name=session["name"], records=records)

# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/predict", methods=["POST"])
def predict():
    if "email" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        msg  = request.get_json().get("message", "").strip()
        if not msg:
            return jsonify({"error": "Empty message"}), 400
        vec  = vectorizer.transform([msg])
        pred = model.predict(vec)[0]
        prob = model.predict_proba(vec)[0]
        result    = "Spam" if pred == 1 else "Ham"
        spam_prob = round(float(prob[1]) * 100, 2)
        ham_prob  = round(float(prob[0]) * 100, 2)
        # save to history
        HISTORY.setdefault(session["email"], []).append({
            "date":    datetime.now().strftime("%d/%m/%Y %H:%M"),
            "message": msg[:80] + ("..." if len(msg) > 80 else ""),
            "result":  result,
            "prob":    spam_prob
        })
        return jsonify({"prediction": result, "spam_prob": spam_prob, "ham_prob": ham_prob})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Spam Detector running!")
    print("  Open: http://127.0.0.1:5000")
    print("  Login: demo@gmail.com / demo123")
    print("="*50 + "\n")
    app.run(debug=True)
