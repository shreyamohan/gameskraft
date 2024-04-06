from typing import Dict, List, Optional
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    password: Optional[str] = None
    latitude: float
    longitude: float
    game_preference: Dict[str, int]  
    scores: Dict[str, int]  
    friends: List[int]
    blocked_users: List[int]

class Games(BaseModel):
    id: int
    name: str

class FriendRequest(BaseModel):
    user_id: int
    friend_id: int