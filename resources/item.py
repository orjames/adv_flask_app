from typing import Dict, List

from flask import request
from flask_restful import Resource
from marshmallow import ValidationError
from flask_jwt_extended import (
    jwt_required,
    fresh_jwt_required,
)
from models.item import ItemModel
from schemas.item import ItemSchema

ERROR_INSERTING = "An error occurred while inserting the item."
ITEM_DELETED = "Item deleted."
ITEM_NOT_FOUND = "Item not found."
NAME_ALREADY_EXISTS = "An item with name '{}' already exists."

item_schema = ItemSchema()


class Item(Resource):
    # making it a classmethod using the @ decorator, doesn't depend on the object that's calling it (aka self)
    # classmethod vs static methods, classmethods give more inheritance benefits, and access to cls
    @classmethod
    def get(cls, name: str):
        item = ItemModel.find_by_name(name)
        if item:
            return item_schema.dump(item), 200
        return {"message": ITEM_NOT_FOUND}, 404

    # classmethod goes above @fresh_jwt_required
    @classmethod
    @fresh_jwt_required
    def post(cls, name: str):  # /item/chair
        if ItemModel.find_by_name(name):
            return {"message": NAME_ALREADY_EXISTS.format(name)}, 400

        item_json = request.get_json()  # price, store_id
        item_json["name"] = name

        try:
            item = item_schema.load(item_json)
        except ValidationError as err:
            return err.messages, 400

        try:
            item.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500

        return item_schema.dump(item), 201

    @classmethod
    @jwt_required
    def delete(cls, name: str):
        item = ItemModel.find_by_name(name)
        if item:
            item.delete_from_db()
            return {"message": ITEM_DELETED}, 200
        return {"message": ITEM_NOT_FOUND}, 404

    @classmethod
    def put(cls, name: str):
        data = Item.parser.parse_args()

        item = ItemModel.find_by_name(name)

        if item:
            item.price = data["price"]
        else:
            item = ItemModel(name, **data)

        item.save_to_db()

        return item.json(), 200


class ItemList(Resource):
    def get(self):
        return {"items": [item.json() for item in ItemModel.find_all()]}, 200
