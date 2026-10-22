"""
Insert sample lost & found posts so the app has data to show.

Usage:
    python seed.py          # add the sample posts
    python seed.py --reset  # delete ALL posts first (asks for confirmation), then add samples
"""

import sys
from datetime import datetime, timedelta, timezone

from app import items


def days_ago(n):
    """Midnight UTC, n days before today."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=n)


SAMPLE_ITEMS = [
    {
        "type": "found",
        "title": "Black AirPods Pro case",
        "description": "Found on a desk near the windows. No name on it.",
        "category": "Electronics",
        "building": "Bobst Library",
        "location": "4th floor, quiet study area",
        "date": days_ago(0),
        "contact": "found.bobst@nyu.edu",
        "status": "open",
    },
    {
        "type": "lost",
        "title": "NYU ID card",
        "description": "Lost my NYU ID, probably after the morning lecture.",
        "category": "ID / Cards",
        "building": "Silver Center",
        "location": "Room 207",
        "date": days_ago(1),
        "contact": "alex.lost@nyu.edu",
        "status": "open",
    },
    {
        "type": "found",
        "title": "Blue Hydro Flask",
        "description": "32 oz, has a cat sticker on the side.",
        "category": "Water Bottles",
        "building": "Kimmel Center",
        "location": "8th floor lounge",
        "date": days_ago(2),
        "contact": "kimmel.helper@nyu.edu",
        "status": "open",
    },
    {
        "type": "lost",
        "title": "Keys with red lanyard",
        "description": "Three keys and a small Eiffel Tower keychain.",
        "category": "Keys",
        "building": "Washington Square Park",
        "location": "Near the fountain",
        "date": days_ago(3),
        "contact": "keys.owner@nyu.edu",
        "status": "open",
    },
    {
        "type": "found",
        "title": "Calculus textbook",
        "description": "Stewart, 8th edition. A name is written inside the cover.",
        "category": "Books / Notes",
        "building": "Warren Weaver Hall",
        "location": "Room 109",
        "date": days_ago(4),
        "contact": "math.finder@nyu.edu",
        "status": "claimed",
    },
    {
        "type": "lost",
        "title": "Gray NYU hoodie",
        "description": "Size M, left on a chair after dinner.",
        "category": "Clothing",
        "building": "Lipton Dining Hall",
        "location": "Near the salad bar",
        "date": days_ago(5),
        "contact": "hoodie.lost@nyu.edu",
        "status": "open",
    },
    {
        "type": "found",
        "title": "Brown leather wallet",
        "description": "Has a MetroCard inside, no cash. Turned in to the front desk.",
        "category": "Wallets / Bags",
        "building": "Paulson Center",
        "location": "Lobby front desk",
        "date": days_ago(6),
        "contact": "paulson.desk@nyu.edu",
        "status": "open",
    },
    {
        "type": "lost",
        "title": "Silver bracelet",
        "description": "Thin chain with a small heart charm. Sentimental value!",
        "category": "Jewelry / Accessories",
        "building": "Tisch Hall",
        "location": "2nd floor restroom",
        "date": days_ago(7),
        "contact": "bracelet.owner@nyu.edu",
        "status": "open",
    },
]


def main():
    if "--reset" in sys.argv:
        # the database is shared by the whole team, so ask before wiping it
        answer = input("This deletes ALL posts in the shared database. Type 'yes' to continue: ")
        if answer.strip().lower() != "yes":
            print("Cancelled.")
            return
        deleted = items.delete_many({}).deleted_count
        print(f"Deleted {deleted} posts.")

    now = datetime.now(timezone.utc)
    docs = []
    for i, item in enumerate(SAMPLE_ITEMS):
        # newest sample first: each one is created a minute earlier than the previous
        created = now - timedelta(minutes=i)
        docs.append({**item, "created_at": created, "updated_at": created})

    result = items.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} sample posts.")


if __name__ == "__main__":
    main()