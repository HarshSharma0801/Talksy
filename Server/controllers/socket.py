import socketio
from prisma import Prisma
from controllers.message import create_message  

class SocketService:
    def __init__(self):
        print("Initiating socket server")
        self.sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="http://localhost:3000")
        self.register_events()

    def register_events(self):
        @self.sio.event
        async def connect(sid, environ, auth=None):  # Add `auth` as an optional argument
            print(f"New Connection: {sid}")
            # You can access `auth` if needed
            if auth:
                print(f"Auth data: {auth}")

        @self.sio.event
        async def disconnect(sid):
            print(f"Client disconnected: {sid}")

        @self.sio.event
        async def join_room(sid, conversation_id):
            await self.sio.enter_room(sid, conversation_id)
            print(f"Client {sid} joined room {conversation_id}")

        @self.sio.event
        async def send_message(sid, data):
            print(data)
            conversation_id = data.get("groupId")
            message = data.get("content")
            data={
                "name":data["name"],
                "content": data["content"],
                "userId": data["userId"],
                "groupId": data["groupId"],
            }
            saved_message = await create_message(data)
            print(saved_message , "savedddd")
            if saved_message["valid"]:
                message_data = saved_message["data"]
                message_data["timestamp"] = message_data["timestamp"].isoformat()
                await self.sio.emit(
                    "message",
                    {"valid": True, "message": message_data},
                    room=conversation_id
                )

    def get_sio(self):
        return self.sio

socket_service = SocketService()