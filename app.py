import os

import pymongo
from bson.errors import InvalidId
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, abort, redirect, request, url_for, flash
from datetime import datetime
import re

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

@app.errorhandler(404)
def page_not_found(error):
    """Show our own styled page instead of Flask's default 404 page."""
    return render_template("404.html"), 404

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

# gets the item and sends it to detail.html
@app.route("/items/<item_id>", methods=["GET"])
def item_detail(item_id): 
    #display one item's details
    item=get_item_or_404(item_id)

    return render_template("detail.html", item=item)


# shows confirmation on GET. On POST, it deletes the item and sends to the user home
@app.route("/items/<item_id>/delete", methods=["GET", "POST"])
def delete_item(item_id): 
    #show deletion confirmation, then delete only after submission
    item=get_item_or_404(item_id)

    if request.method=="POST": 
        items.delete_one({"_id": item["_id"]})
        return redirect(url_for("home"))

    return render_template("delete.html", item=item)

# --C: add + edit ---

# adds new item: GET shows the empty form, POST saves the new item
@app.route("/items/new", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        form = request.form

        # ensures all required fields are present or shows an error
        for field in REQUIRED_FIELDS:
            if not form.get(field):
                return render_template("add.html", form=form, error=f"Field '{field}' is required.")

        # ensures dropdown values are real options
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
        # go to new post's detail page
        return redirect(url_for("item_detail", item_id=str(result.inserted_id)))
    # if GET request, empty form
    return render_template("add.html", form={}, error=None)

# edits existing item which reuses add.html and posts to this route instead of creating a new post
@app.route("/items/<item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    # get the item to edit or return 404 if not found
    item=get_item_or_404(item_id)

    if request.method == "POST":
        form = request.form

        # same validation as add_item
        for field in REQUIRED_FIELDS:
            if not form.get(field):
                return render_template("add.html", form=form, item=item, error=f"Field '{field}' is required.")

        if form["type"] not in ITEM_TYPES or form["building"] not in BUILDINGS:
            return render_template("add.html", form=form, item=item,error="Invalid type or building.")

        now = datetime.now()
        item_date = datetime.strptime(form["date"], "%Y-%m-%d")   

        # update the item in the database
        items.update_one(
            {"_id": item["_id"]},
            {"$set": {
                "type": form["type"],
                "title": form["title"],
                "description": form.get("description"),
                "category": form.get("category"),
                "building": form.get("building"),
                "location": form.get("location"),
                "date": item_date,
                "contact": form["contact"],
                "updated_at": now,
        }},
        )
        flash("Post updated!", "success")
        return redirect(url_for("item_detail", item_id=item_id))

    # if GET request, render the edit form with the current item data
    form = {**item, "date": item["date"].strftime("%Y-%m-%d")}
    return render_template("add.html", form=form, item = item, error=None)



# --- D: search page ---
@app.route("/search", methods=["GET"])
def search():
    """Search items by keyword, type, category, and building."""
    keyword = request.args.get("q", "").strip()
    item_type = request.args.get("type", "")
    category = request.args.get("category", "")
    building = request.args.get("building", "")

    query = {}

    # Keyword search: title or description
    if keyword:
        safe_keyword = re.escape(keyword)
        query["$or"] = [
            {"title": {"$regex": safe_keyword, "$options": "i"}},
            {"description": {"$regex": safe_keyword, "$options": "i"}}
        ]
    
    # Exact match
    if item_type in ITEM_TYPES: query["type"] = item_type
    if category in CATEGORIES: query["category"] = category
    if building in BUILDINGS: query["building"] = building

    # Retrieve matching items, newest first
    results = items.find(query).sort(
        "created_at", pymongo.DESCENDING
    ).limit(50)

    return render_template(
        "search.html",
        items=list(results),
        keyword=keyword,
        selected_type=item_type,
        selected_category=category,
        selected_building=building
    )


if __name__ == "__main__":
    app.run(port=8000, debug=True)