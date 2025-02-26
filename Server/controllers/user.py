# user.py
from fastapi import APIRouter, HTTPException, Query
from prisma import Prisma

router = APIRouter()
prisma = Prisma()

@router.get("/user/{id}")
async def get_user_by_id(id: int):
    await prisma.connect()
    try:
        user = await prisma.user.find_unique(where={"id": id})
        if not user:
            raise HTTPException(status_code=404, detail="Group not found")
        return {"valid": True, "id": user.id}
    except Exception as e:
        print(f"Error fetching group: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        await prisma.disconnect()

@router.get("/user")
async def get_user_by_name(name: str = Query(...)):
    await prisma.connect()
    try:
        if not isinstance(name, str):  # This check is redundant due to type hint, but kept for consistency
            raise HTTPException(status_code=404, detail="user not found")
        user = await prisma.user.find_unique(where={"username": name})
        if not user:
            return {"valid": False, "message": "user not found"}
        return {
            "valid": True,
            "user": {
                "realName": user.name,
                "name": user.username,
                "email": user.email,
                "avatar": user.avatar,
                "id": user.id,
                "isGroup": user.isGroup,
            },
        }
    except Exception as e:
        print(f"Error fetching group: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        await prisma.disconnect()