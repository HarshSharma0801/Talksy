# controllers/message.py
from prisma import Prisma
from datetime import datetime

prisma = Prisma()

async def create_message(message_data: dict):
    await prisma.connect()
    try:
        print(message_data , "message -datatat")
        # Extract required fields
        content = message_data.get("content")
        name = message_data.get("name")
        user_id = message_data.get("userId")
        group_id = message_data.get("groupId")

        # Validate required fields
        if not all([content, name, user_id, group_id]):
            return {
                "data": None,
                "valid": False,
                "message": "All fields are required.",
            }

        # Check if user exists
        user_exists = await prisma.user.find_unique(where={"id": int(user_id)})
        if not user_exists:
            return {
                "data": None,
                "valid": False,
                "message": "User not found.",
            }

        # Check if group exists
        group_exists = await prisma.usergroup.find_unique(where={"id": group_id})
        if not group_exists:
            return {
                "data": None,
                "valid": False,
                "message": "Group not found.",
            }

        # Create the message
        new_message = await prisma.message.create(
            data={
                "content": content,
                "name": name,
                "userId": int(user_id),  # Ensure integer
                "groupId": group_id,     # String UUID
                "timestamp": datetime.now(),  # Matches default(now()) in Prisma
                "avatar": user_exists.avatar, # From user
            }
        )

        return {
            "valid": True,
            "data": new_message.dict(), # Convert Prisma model to dict
            "message": "message created !",
        }

    except Exception as e:
        print(f"Error creating message: {e}")
        return {
            "data": None,
            "valid": False,
            "message": "Internal Server Error",
        }
    finally:
        await prisma.disconnect()