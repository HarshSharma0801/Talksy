# user_group.py
from fastapi import APIRouter, HTTPException, Query
from prisma import Prisma
from pydantic import BaseModel
from uuid import uuid4
from utils.avatar import make_avatar  # Assuming this is in utils/avatar.py
from typing import Union
from datetime import datetime, timezone


router = APIRouter()
prisma = Prisma()

# Pydantic models for request validation
class CreateGroupRequest(BaseModel):
    name: str
    userId: int
    username: str

class CheckMembershipRequest(BaseModel):
    userId: int
    groupId: Union[str, int]
    isGroup: bool

class DeleteGroupRequest(BaseModel):
    groupId: str

@router.post("/createUserGroup")
async def create_user_group(request: CreateGroupRequest):
    await prisma.connect()
    try:
        if not request.name or not request.userId:
            raise HTTPException(status_code=400, detail="Name and userId are required")

        group_code = str(uuid4())
        new_group = await prisma.usergroup.create(
            data={
                "name": request.name,
                "code": group_code,
                "isGroup": True,
                "adminId": request.userId,
                "avatar": make_avatar(),
            }
        )
        user = await prisma.user.find_unique(where={"username": request.username})
        if user:
            member = await prisma.member.create(
                data={
                    "userId": request.userId,
                    "userGroupId": new_group.id,
                    "name": request.username,
                    "avatar": user.avatar,
                }
            )
            return {
                "valid": True,
                "message": "User group created",
                "code": new_group.code,
                "member": member.id,
            }
        # If user not found, we’ll let it fall through to the exception
        raise Exception("User not found")
    except Exception as e:
        print(f"Error creating user group: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await prisma.disconnect()



@router.get("/fetchUserGroups")
async def fetch_groups(userId: int = Query(...)):
    await prisma.connect()
    try:
        if not userId:
            raise HTTPException(status_code=400, detail="User ID is required")

        groups = await prisma.usergroup.find_many(
            where={
                "OR": [
                    {"adminId": userId},
                    {"Member": {"some": {"userId": userId}}},
                ]
            },
            include={
                "Message": {"order_by": {"timestamp": "desc"}, "take": 1},
                "Member": True,  # Fetch all fields of Member
            },
            take=10,
        )

        # Use UTC-aware datetime.min as fallback
        utc_min = datetime.min.replace(tzinfo=timezone.utc)
        sorted_groups = sorted(
            groups,
            key=lambda g: g.Message[0].timestamp if g.Message else utc_min,
            reverse=True
        )
        modified_groups = []
        for group in sorted_groups:
            if not group.isGroup:
                other_member = next(
                    (m for m in group.Member if m.userId != userId), None
                )
                if other_member:
                    group.name = other_member.name or "Unnamed"
                    group.avatar = other_member.avatar
            # Manually select the fields you need from Member
            group.Member = [{"userId": m.userId, "name": m.name, "avatar": m.avatar} for m in group.Member]
            modified_groups.append(group.dict())

        return {"valid": True, "groups": modified_groups}
    except Exception as e:
        print(f"Error fetching user groups: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await prisma.disconnect()


@router.post("/checkUserGroup")
async def check_membership(request: CheckMembershipRequest):
    await prisma.connect()
    try:
        if request.isGroup:
            # Handle group case (groupId is a UUID)
            group = await prisma.usergroup.find_unique(
                where={"id": str(request.groupId)},
                include={
                    "Message": {"order_by": {"timestamp": "desc"}, "take": 20},
                    "Member": True,  # Fetch all fields of Member
                },
            )
            if not group:
                raise HTTPException(status_code=404, detail="Group not found")
            is_member = any(m.userId == request.userId for m in group.Member)
            if not is_member:
                return {"valid": False, "message": "User is not a member of the group"}
            # Manually select fields for Member
            group.Member = [{"userId": m.userId, "name": m.name} for m in group.Member]
            return {"valid": True, "group": group.dict()}
        else:
            # Handle non-group case
            if len(str(request.groupId)) == 36:  # UUID check
                group = await prisma.usergroup.find_unique(
                    where={"id": str(request.groupId)},
                    include={
                        "Message": {"order_by": {"timestamp": "desc"}, "take": 20},
                        "Member": True,  # Fetch all fields of Member
                    },
                )
                if group:
                    other_member = next(
                        (m for m in group.Member if m.userId != request.userId), None
                    )
                    group.adminId = request.userId
                    group.name = other_member.name if other_member else ""
                    group.avatar = other_member.avatar if other_member else ""
                    # Manually select fields for Member
                    group.Member = [{"userId": m.userId, "name": m.name, "avatar": m.avatar} for m in group.Member]
                    return {"valid": True, "group": group.dict()}
            else:
                # Handle case where groupId is an integer (user ID)
                user = await prisma.user.find_unique(where={"id": request.userId})
                other_user = await prisma.user.find_unique(where={"id": int(request.groupId)})
                if not user or not other_user:
                    raise HTTPException(status_code=404, detail="User or other member not found")

                user_group = await prisma.usergroup.find_first(
                    where={
                        "isGroup": False,
                        "Member": {
                            "every": {
                                "OR": [{"userId": user.id}, {"userId": other_user.id}]
                            }
                        },
                    },
                    include={"Member": True, "Message": True},
                )

                if not user_group:
                    new_group = await prisma.usergroup.create(
                        data={
                            "isGroup": False,
                            "adminId": request.userId,
                            "Member": {
                                "create": [
                                    {"userId": user.id, "name": user.username, "avatar": user.avatar},
                                    {"userId": other_user.id, "name": other_user.username, "avatar": other_user.avatar},
                                ]
                            },
                        },
                        include={"Member": True, "Message": True},
                    )
                    new_group.name = other_user.name
                    new_group.avatar = other_user.avatar
                    return {"valid": True, "group": new_group.dict()}
                user_group.name = other_user.name
                user_group.avatar = other_user.avatar
                return {"valid": True, "group": user_group.dict()}
    except Exception as e:
        print(f"Error checking membership: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await prisma.disconnect()

@router.get("/userGroup/{id}")
async def get_user_group_by_id(id: str, userId: int = Query(...)):
    await prisma.connect()
    try:
        user_group = await prisma.usergroup.find_unique(
            where={"id": id},
            include={"Message": True, "Member": True},  # Fetch all fields of Message and Member
        )
        if not user_group:
            return {"valid": False, "message": "group not found"}
        if not user_group.isGroup:
            other_member = next(
                (m for m in user_group.Member if m.userId != userId), None
            )
            user_group.name = other_member.name if other_member else ""
            user_group.avatar = other_member.avatar if other_member else ""
        # Manually include user details for each message
        for message in user_group.Message:
            message_user = await prisma.user.find_unique(where={"id": message.userId})
            message.user = {"id": message_user.id, "name": message_user.name, "avatar": message_user.avatar}
        return {"valid": True, "group": user_group.dict()}
    except Exception as e:
        print(f"Error fetching group: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        await prisma.disconnect()


@router.get("/userGroup")
async def get_user_group_by_name(name: str = Query(...)):
    await prisma.connect()
    try:
        user_groups = await prisma.usergroup.find_many(where={"name": name})
        if not user_groups:
            return {"valid": False, "message": "group not found"}
        return {"valid": True, "group": [g.dict() for g in user_groups]}
    except Exception as e:
        print(f"Error fetching group: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        await prisma.disconnect()

@router.get("/userGroupAdmin")
async def get_user_groups_by_admin(userId: str = Query(...)):
    await prisma.connect()
    try:
        if not userId or not userId.isdigit():
            raise HTTPException(status_code=400, detail="Invalid or missing userId")
        user_groups = await prisma.usergroup.find_many(
            where={"isGroup": True, "adminId": int(userId)}
        )
        if not user_groups:
            return {"valid": False, "message": "No groups found", "groups": None}
        return {"valid": True, "groups": [g.dict() for g in user_groups], "message": "found"}
    except Exception as e:
        print(f"Error fetching user groups: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        await prisma.disconnect()

        
@router.delete("/userGroup")
async def delete_user_group(request: DeleteGroupRequest):
    await prisma.connect()
    try:
        if not request.groupId:
            raise HTTPException(status_code=400, detail="Invalid or missing groupId")
        deleted_group = await prisma.usergroup.delete(where={"id": request.groupId})
        return {
            "valid": True,
            "message": "Group deleted successfully",
            "group": deleted_group.dict(),
        }
    except Exception as e:
        print(f"Error deleting user group: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        await prisma.disconnect()