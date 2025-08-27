import os
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

MONGO_URL = os.getenv("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)

engine = AIOEngine(client=client, database="catcin_db")

