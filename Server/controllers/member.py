# member.py
from fastapi import APIRouter, HTTPException
from prisma import Prisma
from pydantic import BaseModel

router = APIRouter()
prisma = Prisma()

# Pydantic models for request validation
class CreateMemberRequest(BaseModel):
    userId: int
    groupId: str
    code: str

class DeleteMemberRequest(BaseModel):
    memberId: int

@router.post("/createMember")
async def create_member(request: CreateMemberRequest):
    await prisma.connect()
    try:
        if not request.userId or not request.groupId or not request.code:
            return {
                "message": "Invalid group or code.",
                "valid": False,
                "newMember": None,
            }

        group = await prisma.usergroup.find_unique(where={"id": request.groupId})
        user = await prisma.user.find_unique(where={"id": request.userId})

        if not group or group.code != request.code or (not group.isGroup and not user):
            return {
                "message": "Invalid group or code.",
                "valid": False,
                "newMember": None,
            }

        new_member = await prisma.member.create(
            data={
                "userId": request.userId,
                "userGroupId": request.groupId,
                "name": user.username if user else "Default Name",
                "avatar": user.avatar if user else None,
            }
        )

        return {
            "message": "Member created successfully.",
            "newMember": new_member.dict(),
            "valid": True,
        }
    except Exception as e:
        print(f"Error creating member: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
    finally:
        await prisma.disconnect()

@router.post("/deleteMember")
async def delete_member(request: DeleteMemberRequest):
    await prisma.connect()
    try:
        member = await prisma.member.delete(where={"id": request.memberId})
        return {
            "message": "Member deleted successfully.",
            "valid": True,
            "member": member.dict(),
        }
    except Exception as e:
        print(f"Error deleting member: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
    finally:
        await prisma.disconnect()