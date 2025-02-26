import { io, Socket } from "socket.io-client";

let socket: Socket;

export const getSocket = (): Socket => {
  socket = io("http://localhost:7070", { 
    autoConnect: false,
    withCredentials: true,
    transports: ["websocket", "polling"]
  });
  return socket;
};