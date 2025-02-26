# auth.py
from fastapi import APIRouter, HTTPException, Request
from prisma import Prisma
from jose import jwt
from pydantic import BaseModel
import os
from utils.avatar import make_avatar

router = APIRouter()
prisma = Prisma()
JWT_SECRET = os.getenv("JWT_ACCESS", "default")

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    username: str

class LoginRequest(BaseModel):
    username: str
    password: str



@router.post("/signup")
async def signup(request: SignupRequest):
    await prisma.connect()
    try:
        # Check for existing user
        existing_user = await prisma.user.find_first(
            where={"OR": [{"username": request.username}, {"email": request.email}]}
        )
        if existing_user:
            return {"msg": "try different username or email", "valid": False}

        # Create new user
        user = await prisma.user.create(
            data={
                "name": request.name,
                "email": request.email,
                "password": request.password,  # Hash in production!
                "username": request.username,
                "isGroup": False,
                "avatar": make_avatar(),
            }
        )
        return {"msg": "User added", "valid": True, "username": user.username}
    finally:
        await prisma.disconnect()

@router.post("/login")
async def login(request: LoginRequest):
    await prisma.connect()
    try:
        user = await prisma.user.find_first(
            where={"username": request.username, "password": request.password}
        )
        if not user:
            return {"valid": False}

        token = jwt.encode({"Userdata": user.dict()}, JWT_SECRET, algorithm="HS256")
        return {"access": token, "UserInfo": user.dict(), "valid": True}
    finally:
        await prisma.disconnect()

@router.get("/token")
async def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or "Bearer " not in auth_header:
        return {"valid": False}

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"UserInfo": payload, "valid": True}
    except Exception:
        return {"valid": False}