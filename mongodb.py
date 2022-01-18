import motor.motor_asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from bson.objectid import ObjectId
MONGO_DETAILS = 'mongodb+srv://admin:admin@cluster0.dauoh.mongodb.net/agora?retryWrites=true&w=majority'
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS, uuidRepresentation="standard")

chat = client.chat

chat_collection  = chat.get_collection('chat_collection')


class Mongo:
    def __init__(self, collection, helper):
        self.collection = collection
        self.helper = helper

    async def get(self, limit:int, offset:int, query:dict):
        collection = self.collection.find(query)
        count = await self.collection.count_documents(query)
        data = []
        async for item in collection.skip(offset).limit(limit):
            data.append(self.helper(item))
        return {'data': data, 'count': count}

    # Add a new student into to the database
    async def add(self, body: dict) -> dict:
        data = await self.collection.insert_one(body)
        new_data = await self.collection.find_one({"_id": data.inserted_id})
        return self.helper(new_data)

    # Retrieve a student with a matching ID
    async def retrieve(self, id: str) -> dict:
        data = await self.collection.find_one({"_id": ObjectId(id)})
        if data:
            return self.helper(data)


    # Update a student with a matching ID
    async def update(self, id: str,data: dict, model_name, collection_to_be_updated):
        # Return false if an empty request body is sent.
        if len(data) < 1:
            return False
        update_object = await self.collection.find_one({"_id": ObjectId(id)})

        if update_object:
            for item in collection_to_be_updated:
                updated_many = await item.update_many(
                    {f"{model_name}.id": str(update_object['_id'])}, {"$set": data['data']['update_many']}
                )
                print(model_name)
            updated_one = await self.collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data['data']['update_one']}
            )
            
            if updated_many:
                return True
            return False


    # Delete a student from the database
    async def delete(self, id: str):
        student = await self.collection.find_one({"_id": ObjectId(id)})
        if student:
            await self.collection.delete_one({"_id": ObjectId(id)})
            return True