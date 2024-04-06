from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "gameskraft"

app = FastAPI()

# MongoDB connection setup
@app.on_event("startup")
async def startup_db_client():
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
        app.mongodb = app.mongodb_client[MONGO_DB]
    except Exception as e:
        print(e)

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Example route to test MongoDB connection
@app.get("/")
async def read_root():
    collection = app.mongodb["users"]
    
    async for document in collection.find():
            print(document)
    return {"message": "Hello, FastAPI!", "data_from_mongodb": "hey"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)