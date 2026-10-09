import os

import pymongo
from dotenv import load_dotenv
from flask import Flask, render_template, request

from constants import BUILDINGS, CATEGORIES, ITEM_TYPES, STATUSES

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DBNAME")]
items = db.items

@app.context_processor
def inject_constants():
    """Make the dropdown lists available in every template."""
    return {
        "ITEM_TYPES": ITEM_TYPES,
        "STATUSES": STATUSES,
        "CATEGORIES": CATEGORIES,
        "BUILDINGS": BUILDINGS,
    }

# --- A: home / list page ---
@app.route("/")
def home():
    """List recent posts, optionally filtered by ?type=lost or ?type=found."""
    item_type = request.args.get("type")
    if item_type not in ITEM_TYPES:
        item_type = None  # ignore missing or invalid values, show everything

    query = {"type": item_type} if item_type else {}
    recent = items.find(query).sort("created_at", pymongo.DESCENDING).limit(50)
    return render_template("index.html", items=list(recent), active_type=item_type)

if __name__ == "__main__":
    app.run(port=8000, debug=True)