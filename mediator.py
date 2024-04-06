from math import radians, cos, sin, asin, sqrt
from fastapi.responses import JSONResponse
import json
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from fastapi import HTTPException

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)*2 + cos(lat1) * cos(lat2) * sin(dlon/2)*2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def check_match(gamer1, gamer2):
    # Retrieve the scores for each gamer
    gamer1_scores = gamer1.get('scores', {})
    gamer2_scores = gamer2.get('scores', {})
    
    # Identify all games either gamer has played
    gamer1_games = set(gamer1_scores.keys())
    gamer2_games = set(gamer2_scores.keys())
    
    # Check if both gamers have played the same games
    if gamer1_games != gamer2_games:
        return False
    
    # Check the score difference for each game
    for game in gamer1_games:
        score1 = gamer1_scores[game]
        score2 = gamer2_scores[game]
        
        if abs(score1 - score2) > 10:
            return False
    
    # If all checks pass, return True
    return True

async def findPreference(user_id, users_collection):
    """
    Fetches the game preference of a user by their ID.
    """
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    game_preference = user.get("scores")
    return jsonable_encoder(game_preference)


async def findMatchedUser(id,users_collection):
    user_preference= await findPreference(id,users_collection)

    if not user_preference:
        user_preference= []

    print("user_preference",user_preference)

    # Fetch all gamers except the one with the specified id
    gamers = []
    async for gamer in users_collection.find({"id": {"$ne": id}}):
        gamers.append(gamer)

    print("gamers",gamers)

    matched_groups = []
    for i, gamer1 in enumerate(gamers):
        for gamer2 in gamers[i+1:]:
            if check_match(gamer1, gamer2):
                # Check if either gamer is already in a group
                found_group = False
                for group in matched_groups:
                    if gamer1['id'] in group['ids'] or gamer2['id'] in group['ids']:
                        group['ids'].update([gamer1['id'], gamer2['id']])
                        group['names'].update([gamer1['name'], gamer2['name']])
                        found_group = True
                        break
                if not found_group:
                    matched_groups.append({
                        'ids': set([gamer1['id'], gamer2['id']]),
                        'names': set([gamer1['name'], gamer2['name']])
                    })

    print("matched_groups",matched_groups)
    output_groups=[]
    for group in matched_groups:
        group_ids = list(group['ids'])
        group_names = list(group['names'])

        for id, name in zip(group_ids, group_names):
            output_groups.append({
                "id": id,
                "name": name
            })

    return output_groups