import os

import pymongo
from bson.errors import InvalidId
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, abort, redirect, request, url_for

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

@app.route("/")
def home():
    recent = items.find().sort("created_at", pymongo.DESCENDING).limit(50)
    return render_template("index.html", items=list(recent))


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


if __name__ == "__main__":
    app.run(port=8000, debug=True)