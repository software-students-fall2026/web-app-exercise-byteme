import os

import pymongo
from bson.errors import InvalidId
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, abort, redirect, request, url_for, flash
from datetime import datetime

from constants import BUILDINGS, CATEGORIES, ITEM_TYPES, STATUSES

REQUIRED_FIELDS = ["type", "title", "building", "date", "contact"]

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


# --B: detail + delete ---


# this function is for finding item. Returns 404 if its ID is invalid or missing
def get_item_or_404(item_id):
    "Find an item, or return a 404 if its ID is invalid or missing."
    try:
        object_id = ObjectId(item_id)
    except (InvalidId, TypeError):
        abort(404)

    item = items.find_one({"_id": object_id})

    if item is None:
        abort(404)

    return item

#gets the item and sends it to detail.html
@app.route("/items/<item_id>", methods=["GET"])
def item_detail(item_id): 
    #display one item's details
    item=get_item_or_404(item_id)

    return render_template("detail.html", item=item)


#shows confirmation on GET. On POST, it deletes the item and sends to the user home
@app.route("/items/<item_id>/delete", methods=["GET", "POST"])
def delete_item(item_id): 
    #show deletion confirmation, then delete only after submission
    item=get_item_or_404(item_id)

    if request.method=="POST": 
        items.delete_one({"_id": item["_id"]})
        return redirect(url_for("home"))

    return render_template("delete.html", item=item)

# --C: add + edit ---

@app.route("/items/new", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        form = request.form
        # ensures all required fields are present
        for field in REQUIRED_FIELDS:
            if not form.get(field):
                return render_template("add.html", form=form, error=f"Field '{field}' is required.")

        if form["type"] not in ITEM_TYPES or form["building"] not in BUILDINGS:
            return render_template("add.html", form=form, error="Invalid type or building.")

        now = datetime.now()   
        item = {
            "type": form["type"],
            "title": form["title"],
            "description": form["description"],
            "category": form["category"],
            "building": form["building"],
            "location": form["location"],
            "date": datetime.strptime(form["date"], "%Y-%m-%d"),
            "contact": form["contact"],
            "status": "open",
            "created_at": now,
            "updated_at": now,
        }
        result = items.insert_one(item)
        flash("Post created!", "success")
        return redirect(url_for("item_detail", item_id=str(result.inserted_id)))

    return render_template("add.html", form={}, error=None)

@app.route("/items/<item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    # get the item to edit or return 404 if not found
    item=get_item_or_404(item_id)

    if request.method == "POST":
        form = request.form
        # edits required fields
        for field in REQUIRED_FIELDS:
            if not form.get(field):
                return render_template("add.html", form=form, error=f"Field '{field}' is required.")

        if form["type"] not in ITEM_TYPES or form["building"] not in BUILDINGS:
            return render_template("add.html", form=form, error="Invalid type or building.")

        now = datetime.now()   
        items.update_one(
            {"_id": item["_id"]},
            {"$set": {
                "type": form["type"],
                "title": form["title"],
                "description": form.get("description"),
                "category": form.get("category"),
                "building": form.get("building"),
                "location": form.get("location"),
                "date": item["date"],
                "contact": form["contact"],
                "status": "open",
                "updated_at": now,
        }},
        )
        return redirect(url_for("item_detail", item_id=item_id))

    # if GET request, render the edit form with the current item data
    form = {**item, "date": item["date"].strftime("%Y-%m-%d")}
    return render_template("add.html", form=form, item = item, error=None)



if __name__ == "__main__":
    app.run(port=8000, debug=True)