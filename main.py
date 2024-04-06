from fastapi import FastAPI,APIRouter,Depends,Request
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
import json
from models import FriendRequest
from mediator import findMatchedUser
from sse_starlette.sse import EventSourceResponse
import asyncio


# MongoDB configuration
MONGO_URI = "mongodb+srv://shreyamohan283:OGBQN0GSXTqtXakA@cluster0.apv7ktv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB = "gamescommunity"
users_collection=[]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from all origins (you can specify specific origins instead)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allow these HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# MongoDB connection setup
@app.on_event("startup")
async def startup_db_client():
    try:
        global users_collection
        app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
        app.mongodb = app.mongodb_client[MONGO_DB]      
        users_collection=app.mongodb["users"]  
    except Exception as e:
        print(e)

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Example route to test MongoDB connection
@app.get("/friendrequests/{u_id}")
async def friendrequests(u_id: int):
    collection = app.mongodb["users"]
    friendrequests=[]
    friendetails=[]
    friendrequests=await collection.find_one({"id":u_id})
    for item in friendrequests['friendrequests']:
         friendetails.append(await collection.find_one({"id":item}))

    details=[{"id":item['id'],"name":item['name']} for item in friendetails]
    return json.dumps({"status": 200, "data": details})

@app.get("/friends/{u_id}")
async def friends(u_id: int):
    collection = app.mongodb["users"]
    friendrequests=[]
    friendetails=[]
    friendrequests=await collection.find_one({"id":u_id})
    for item in friendrequests['friends']:
         friendetails.append(await collection.find_one({"id":item}))

    details=[{"id":item['id'],"name":item['name']} for item in friendetails]
    return json.dumps({"status": 200, "data": details})


@app.get("/api/get-matching-gamers/{id}")
async def create_item(id:int):
    matched_user= await findMatchedUser(id,users_collection)
    return matched_user

# POST endpoint to add a new user
@app.post("/api/users")
async def add_user(user: Request):
    user_dict = await user.json()
    result = await users_collection.insert_one(user_dict)
    return "User added successfully"

@app.post("/acceptfriendrequest")
async def accept_fr(fr:FriendRequest):
    collection = app.mongodb["users"]
    user_data=await collection.find_one({"id":fr.user_id})
        
    user_data['friends'].append(fr.friend_id)
        
    filter_criteria = {"id":fr.user_id}
    update_operation = {"$set": user_data}

    result = collection.update_one(filter_criteria, update_operation)

    user_data=await collection.find_one({"id":fr.friend_id})    

    user_data['friends'].append(fr.user_id)
    try:
        user_data['friendrequests'].remove(fr.user_id)
    except:
        return json.dumps({"status": 500,"error":'This user did not send the request'})
    
    filter_criteria = {"id":fr.friend_id}
    update_operation = {"$set": user_data}
    result = collection.update_one(filter_criteria, update_operation)
    return json.dumps({"status": 200})

@app.post("/rejectfriendrequest")
async def reject_fr(fr:FriendRequest):
    collection = app.mongodb["users"]
    user_data=await collection.find_one({"id":fr.user_id})
        
    user_data['friendrequests'].remove(fr.friend_id)
    
    filter_criteria = {"id":fr.user_id}
    update_operation = {"$set": user_data}

    result = collection.update_one(filter_criteria, update_operation)

    user_data=await collection.find_one({"id":fr.friend_id})    

    
    filter_criteria = {"id":fr.friend_id}
    update_operation = {"$set": user_data}
    result = collection.update_one(filter_criteria, update_operation)
    return json.dumps({"status": 200})


@app.post("/sendfriendrequest")
async def send_fr(fr:FriendRequest):
    collection = app.mongodb["users"]
    user_data=await collection.find_one({"id":fr.friend_id})
        
    user_data['friendrequests'].append(fr.user_id)

    try:
        user_data['suggestions'].remove(fr.friend_id)
    except:
        pass

    try:
        user_data['suggestions'].remove(fr.user_id)
    except:
        pass

    filter_criteria = {"id":fr.friend_id}
    update_operation = {"$set": user_data}
    result = collection.update_one(filter_criteria, update_operation)
    return "Success"

@app.post("/updatescore/{u_id}/{game_name}")
async def update_score(u_id:int,game_name:str,score:int):
    collection = app.mongodb["users"]
    user_data=await collection.find_one({"id":u_id})

    games = app.mongodb["games"]
    gamedata=await games.find_one({"name":game_name})    
    user_data['scores'][str(gamedata['id'])]=score

    filter_criteria = {"id":u_id}
    update_operation = {"$set": user_data}
    result = collection.update_one(filter_criteria, update_operation)
    return "Success"

@app.post("/")
async def root():    
    return "Happy coding!"

async def generate_events():        
    for item in range(0,10):
        yield f"data: Event {item} \n\n"
        await asyncio.sleep(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)