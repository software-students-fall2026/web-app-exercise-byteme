from flask_login import UserMixin
from bson.objectid import ObjectId
from bson.errors import InvalidId

class User(UserMixin):
    def __init__(self, user_document):
        self.id = str(user_document["_id"])
        self.email = user_document["email"]
        self.password_hash = user_document["password_hash"]

    @staticmethod
    def find_by_id(users_collection, user_id):
        try:
            object_id = ObjectId(user_id)
        except (InvalidId, TypeError):
            return None

        document = users_collection.find_one({"_id": object_id})
        if document: return User(document)
        else: return None

    @staticmethod
    def find_by_email(users_collection, email):
        document = users_collection.find_one({"email": email})
        return User(document) if document else None
