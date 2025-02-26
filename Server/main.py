from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import uvicorn
from prisma import Prisma
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import socketio
from controllers.auth import router as auth_router
from controllers.user import router as user_router
from controllers.user_group import router as group_router
from controllers.socket import socket_service
from controllers.member import router as member_router

load_dotenv()

# Lifespan manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect Prisma on startup
    prisma = Prisma()
    try:
        await prisma.connect()
        print("Prisma connected successfully")
    except Exception as e:
        print(f"Failed to connect to Prisma: {e}")
        raise
    app.state.prisma = prisma
    
    # Initialize Socket.IO
    sio = socket_service.get_sio()
    socket_app = socketio.ASGIApp(sio)
    app.mount("/socket.io", socket_app)
    
    yield
    # Disconnect Prisma on shutdown
    await prisma.disconnect()
    print("Prisma disconnected")

app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic endpoint
@app.get("/")
async def root():
    return {"message": "its working"}

# Include routers
router = APIRouter()
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(group_router)
router.include_router(member_router)

app.include_router(router)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7070))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)