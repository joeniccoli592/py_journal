# ✅ Import standard libraries
import os
import sqlite3
from datetime import datetime

# ✅ Load environment variables BEFORE using them
from dotenv import load_dotenv
load_dotenv()

# ✅ THEN import and configure OpenAI (v1.x)
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # v1.x syntax

# ✅ Flask imports
from flask import Flask, request, jsonify  # Flask framework and tools to handle requests/responses
from flask_cors import CORS  # Module to enable Cross-Origin Resource Sharing (CORS)

# Initialize the Flask application
app = Flask(__name__)

# ✅ Allow cross-origin requests from frontend (http://localhost:8000)
# This is necessary so the browser lets the frontend talk to this backend
# ✅ Allow CORS from frontend for all routes (not just /analyze)
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}},  # Only allow /analyze route from localhost:8000
    methods=["GET", "POST", "OPTIONS"],  # Accept only GET, POST, and preflight OPTIONS
    allow_headers=["Content-Type"],  # Allow content type to be JSON
    supports_credentials=True  # Support cookies/auth if needed in future
)

# ✅ Print the absolute path of the SQLite file
print("📌 Creating/Using DB at:", os.path.abspath("journal.db"))

# ✅ Create the SQLite table if it doesn't exist
def init_db():
    conn = sqlite3.connect("journal.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry TEXT NOT NULL,
            summary TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the DB when the app starts
init_db()

# ✅ Save an entry into the SQLite database with error logging
def save_entry(entry, summary):
    try:
        conn = sqlite3.connect("journal.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO entries (entry, summary, timestamp)
            VALUES (?, ?, ?)
        ''', (entry, summary, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        print("✅ Entry saved.")
    except Exception as e:
        print("❌ DB Save Error:", str(e))

# 📡 Basic home route just to test server
@app.route('/', methods=["GET"])
def home():
    return "Welcome to the AI Journal!"  # Just a welcome string when you visit localhost:5000

# 📬 Main route the frontend calls when submitting text
@app.route('/analyze', methods=["POST", "OPTIONS"])
def analyze():
    # 🔐 If the browser sends a preflight request, approve it with status 200
    if request.method == "OPTIONS":
        return ('', 200)

    # 📨 Parse JSON body sent from JavaScript fetch()
    data = request.get_json()

    # 📝 Safely extract 'entry' from the JSON (default to empty string if missing)
    entry = data.get("entry", "")

    # 🧠 Use the OpenAI API (v1.x client) to get a summarized and corrected version of the journal entry
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes, updates grammar, and corrects punctuation in journal entries."},
                {"role": "user", "content": entry}
            ],
            max_tokens=100,
            temperature=0.7
        )

        # ✅ Extract AI's response from the API call
        summary = response.choices[0].message.content.strip()
        save_entry(entry, summary)  # Save to the database

        # 🔁 Return the result back to the browser as a JSON response
        return jsonify({"summary": summary})

    except Exception as e:
        # ❌ Return error message if something goes wrong
        return jsonify({"summary": f"Error: {str(e)}"})

# 📜 Route to retrieve journal history from SQLite
@app.route('/history', methods=["GET"])
def history():
    conn = sqlite3.connect("journal.db")
    cursor = conn.cursor()
    cursor.execute('SELECT entry, summary, timestamp FROM entries ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()

    # Format rows into JSON
    entries = [{"entry": r[0], "summary": r[1], "timestamp": r[2]} for r in rows]
    return jsonify(entries)

# 🚀 Run the app locally on port 5000 in debug mode (auto-restarts on save)
if __name__ == "__main__":
    app.run(debug=True)
